import json
import os
from typing import Any, Dict, List

from ..core import ollama_client


async def classify_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Classify scan items using Ollama LLM, with a deterministic fallback.

    Each input item should be a dict containing at least:
    {"id": str, "category": str, "confidence": float, "title"?, "snippet"?, "url"?, "metadata"?}

    Returns a list of dicts:
    {
      "item_id": str,
      "category": str,
      "risk_score": float,
      "rationale": str,
      "evidence_citations": [ {"url": str, "snippet": str, "confidence": float} ],
      "verifiable": bool,
    }

    If Ollama is unavailable or MOCK_CONNECTORS=true, this falls back to a
    simple rule-based classification so the pipeline still runs.
    """

    mock_mode = os.getenv("MOCK_CONNECTORS", "false").lower() == "true"

    if mock_mode:
        return _fallback_classification(items)

    # Check if Ollama is available
    ollama_ok = await ollama_client.is_available()
    if not ollama_ok:
        return _fallback_classification(items)

    system_content = (
        "You are a privacy risk analyst. For each item, classify its risk. "
        "Return ONLY a JSON array of objects with keys: "
        "item_id, category, risk_score (0-1), rationale, evidence_citations, verifiable. "
        "Each evidence_citation must have url, snippet, confidence (0-1). "
        "Use only the provided evidence (title, snippet, url, metadata)."
    )

    user_payload = {"items": items}
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    try:
        parsed = await ollama_client.chat_completion_json(messages, temperature=0.0)
        if not isinstance(parsed, list):
            raise ValueError("LLM did not return a JSON array")

        normalized: List[Dict[str, Any]] = []
        for item_in, cls in zip(items, parsed):
            item_id = str(cls.get("item_id") or item_in.get("id"))
            category = str(cls.get("category") or item_in.get("category") or "unknown")
            risk_score = float(cls.get("risk_score", 0.0))
            rationale = str(cls.get("rationale") or "")
            citations = cls.get("evidence_citations") or []
            if not citations:
                citations = [
                    {
                        "url": item_in.get("url", ""),
                        "snippet": (item_in.get("snippet") or "")[:300],
                        "confidence": float(item_in.get("confidence", 0.5)),
                    }
                ]
            verifiable = bool(cls.get("verifiable", True))
            normalized.append(
                {
                    "item_id": item_id,
                    "category": category,
                    "risk_score": risk_score,
                    "rationale": rationale,
                    "evidence_citations": citations,
                    "verifiable": verifiable,
                }
            )
        return normalized
    except Exception:
        return _fallback_classification(items)


def _fallback_classification(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deterministic rule-based scoring used when LLM is unavailable or fails."""

    results: List[Dict[str, Any]] = []
    for item in items:
        base_cat = item.get("category") or "unknown"
        conf = float(item.get("confidence", 0.5))

        if base_cat == "breach":
            risk = min(1.0, 0.7 + 0.3 * conf)
        elif base_cat in {"image_match", "social_post"}:
            risk = 0.4 + 0.4 * conf
        else:
            risk = 0.2 + 0.3 * conf

        url = item.get("url", "")
        snippet = item.get("snippet", "")

        results.append(
            {
                "item_id": str(item.get("id")),
                "category": base_cat,
                "risk_score": float(risk),
                "rationale": "Rule-based fallback classification based on item category and confidence.",
                "evidence_citations": [
                    {
                        "url": url,
                        "snippet": snippet[:300],
                        "confidence": float(conf),
                    }
                ],
                "verifiable": True,
            }
        )

    return results
