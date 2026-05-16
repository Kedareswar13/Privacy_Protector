import os
from typing import List, Dict, Any

import httpx


async def search_web(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search the web using Serper.dev (Google Search JSON API).

    If SERPER_API_KEY is not set, fall back to the previous mock behavior so the
    rest of the agent pipeline still works for demos.
    """

    mock_mode = os.getenv("MOCK_CONNECTORS", "false").lower() == "true"
    serper_key = os.getenv("SERPER_API_KEY")

    # If we are explicitly in mock mode or have no Serper key, keep the
    # deterministic mock behavior.
    if mock_mode or not serper_key:
        return [
            {
                "title": f"Mock result for {query}",
                "snippet": f"This is a mock snippet about {query}",
                "url": f"https://example.com/mock/{query.replace(' ', '%20')}",
                "date": "2024-01-01",
            }
        ]

    # Real web search using Serper.dev
    headers = {
        "X-API-KEY": serper_key,
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "q": query,
        "num": limit,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://google.serper.dev/search", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        return [{
            "title": "⚠️ Search Timeout",
            "snippet": "The search service took too long to respond. Please try again later.",
            "url": "",
            "date": ""
        }]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            return [{
                "title": "⚠️ Search Rate Limit Exceeded",
                "snippet": "We have hit the rate limit for the search API. Please wait a moment before trying again.",
                "url": "",
                "date": ""
            }]
        elif exc.response.status_code in [401, 403]:
            return [{
                "title": "⚠️ Search Authentication Error",
                "snippet": "The search API key is invalid or missing. Please check your configuration.",
                "url": "",
                "date": ""
            }]
        return [{
            "title": f"⚠️ Search Error ({exc.response.status_code})",
            "snippet": f"The search service returned an error: {exc.response.text}",
            "url": "",
            "date": ""
        }]
    except httpx.RequestError:
        return [{
            "title": "⚠️ Search Connection Error",
            "snippet": "Could not connect to the search service. Please check your network connection.",
            "url": "",
            "date": ""
        }]
    except Exception as exc:
        return [{
            "title": "⚠️ Unexpected Search Error",
            "snippet": f"An unexpected error occurred during the search: {str(exc)}",
            "url": "",
            "date": ""
        }]

    organic = data.get("organic", []) or []
    results: List[Dict[str, Any]] = []
    for item in organic[:limit]:
        results.append(
            {
                "title": item.get("title") or "",
                "snippet": item.get("snippet") or item.get("description") or "",
                "url": item.get("link") or item.get("url") or "",
                "date": item.get("date") or "",
            }
        )

    # Fallback in case Serper returns no organic results.
    if not results:
        results.append(
            {
                "title": f"No web results found for {query}",
                "snippet": "Try refining your query or adding more identifying details.",
                "url": "",
                "date": "",
            }
        )

    return results