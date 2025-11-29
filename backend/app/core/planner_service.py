import json
import os
from pathlib import Path
from typing import Any, Dict

from openai import AsyncOpenAI


_PLANNER_FEWSHOTS_PATH = Path(__file__).parent / "planner_fewshots.json"


async def _load_fewshots() -> Dict[str, Any]:
    with _PLANNER_FEWSHOTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


async def get_plan(state: Dict[str, Any], goal: str = "produce_risk_report") -> Dict[str, Any]:
    """Return a planner JSON plan.

    If OPENAI_API_KEY is set and MOCK_CONNECTORS is not true, call OpenAI.
    Otherwise, return the first example output from planner_fewshots.json.
    """

    data = await _load_fewshots()
    system_prompt: str = data.get("system_prompt", "")
    examples = data.get("examples", [])

    # Fallback: deterministic mock plan from first example
    def _mock_plan() -> Dict[str, Any]:
        if examples:
            example = examples[0]
            return example.get("output", {"actions": [], "stop": True})
        return {"actions": [], "stop": True}

    api_key = os.getenv("OPENAI_API_KEY")
    mock_mode = os.getenv("MOCK_CONNECTORS", "false").lower() == "true"

    if not api_key or mock_mode:
        return _mock_plan()

    client = AsyncOpenAI(api_key=api_key)

    # Build few-shot messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for ex in examples:
        ex_in = ex.get("input", {})
        ex_out = ex.get("output", {})
        messages.append(
            {
                "role": "user",
                "content": json.dumps(ex_in, ensure_ascii=False),
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(ex_out, ensure_ascii=False),
            }
        )

    # Current state as final user message
    current_input = {"state": state, "goal": goal}
    messages.append(
        {"role": "user", "content": json.dumps(current_input, ensure_ascii=False)}
    )

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",  # small, cheap planner model
            messages=messages,
            temperature=0.1,
        )
        content = resp.choices[0].message.content or "{}"
        plan = json.loads(content)
        # Basic shape fallback
        if "actions" not in plan or "stop" not in plan:
            return _mock_plan()
        return plan
    except Exception:
        # In case of any error, fall back to mock plan
        return _mock_plan()
