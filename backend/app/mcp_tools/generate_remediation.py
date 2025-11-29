import os
from typing import Dict, Any
from openai import AsyncOpenAI

from ..core.pseudonymize import pseudonymize_identifier, pseudonymize_text


async def generate_remediation(item_id: str, tone: str = "polite") -> Dict[str, Any]:
    if os.getenv("MOCK_CONNECTORS", "false").lower() == "true":
        return {
            "draft_email": f"Mock {tone} email for item {item_id}",
            "steps": [f"Mock step 1 for {item_id}", "Mock step 2"],
            "settings_links": [f"https://example.com/settings/{item_id}"]
        }

    # Real implementation placeholder: use pseudonymized identifiers only
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = AsyncOpenAI(api_key=api_key)
    pseudo_item = pseudonymize_identifier(item_id)

    system_prompt = (
        "You are DataSteward Remediation Assistant. NEVER include raw PII in outputs. "
        "Use placeholders like [USER_1], [EMAIL_1]. For the provided pseudonymized item, "
        "produce JSON: { \"draft_email\":\"...\",\"steps\":[""...""],\"settings_links\":[""...""] }."
    )

    # NOTE: to keep scope focused, we still raise NotImplementedError
    # so no actual OpenAI call is made in non-mock mode yet.
    raise NotImplementedError("Non-mock remediation generation not yet implemented")