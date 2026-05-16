"""Thin wrapper around the local Ollama HTTP API.

Every backend module that previously used AsyncOpenAI should import from here
instead.  The base URL defaults to http://localhost:11434 (standard Ollama
port) and can be overridden via the OLLAMA_BASE_URL env var.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:latest")


def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks that qwen3.5 produces."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


async def chat_completion(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.3,
    timeout: float = 300.0,
) -> str:
    """Send a chat-completion request to the local Ollama server.

    Returns the assistant's reply as a plain string.
    """

    model = model or OLLAMA_MODEL
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise RuntimeError("The request to the local AI model timed out. It might be overloaded or still loading.")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise RuntimeError("Rate limit exceeded for the AI model. Please wait a moment and try again.")
        raise RuntimeError(f"AI model returned an error: {exc.response.status_code} - {exc.response.text}")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Failed to connect to the local AI model at {OLLAMA_BASE_URL}. Is it running?")
    except Exception as exc:
        raise RuntimeError(f"An unexpected error occurred while contacting the AI model: {str(exc)}")

    content = data.get("message", {}).get("content", "")
    return _strip_think_tags(content)


async def chat_completion_json(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.1,
    timeout: float = 300.0,
) -> Any:
    """Like chat_completion but attempts to parse the reply as JSON.

    Falls through to raw text if parsing fails.
    """

    raw = await chat_completion(
        messages, model=model, temperature=temperature, timeout=timeout
    )

    try:
        # Strip markdown code fences that LLMs sometimes wrap their JSON in.
        text = raw.strip()
        if text.startswith("```"):
            lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
            text = "\n".join(lines)

        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("The AI model returned an invalid JSON format.")
    except Exception as exc:
        raise RuntimeError(f"Failed to parse AI response: {str(exc)}")


async def is_available() -> bool:
    """Check whether the local Ollama server is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
