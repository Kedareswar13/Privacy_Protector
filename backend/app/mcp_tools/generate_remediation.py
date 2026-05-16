import os
from typing import Dict, Any

from ..core import ollama_client
from ..core.pseudonymize import pseudonymize_identifier


async def generate_remediation(item_id: str, tone: str = "polite") -> Dict[str, Any]:
    if os.getenv("MOCK_CONNECTORS", "false").lower() == "true":
        return {
            "draft_email": f"Mock {tone} email for item {item_id}",
            "steps": [f"Mock step 1 for {item_id}", "Mock step 2"],
            "settings_links": [f"https://example.com/settings/{item_id}"]
        }

    # Check if Ollama is reachable; if not, return a sensible template
    ollama_ok = await ollama_client.is_available()
    if not ollama_ok:
        return _template_remediation(item_id, tone)

    pseudo_item = pseudonymize_identifier(item_id)

    system_prompt = (
        "You are DataSteward Remediation Assistant. NEVER include raw PII in outputs. "
        "Use placeholders like [USER_1], [EMAIL_1]. For the provided pseudonymized item, "
        "produce JSON with exactly these keys: draft_email (string), steps (array of strings), "
        "settings_links (array of URL strings). The tone should be: " + tone + "."
    )

    user_content = (
        f"Generate a remediation plan for item {pseudo_item}. "
        "Return ONLY the JSON object."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    try:
        result = await ollama_client.chat_completion_json(messages, temperature=0.3)
        if isinstance(result, dict) and "draft_email" in result:
            return result
        return _template_remediation(item_id, tone)
    except Exception:
        return _template_remediation(item_id, tone)


def _template_remediation(item_id: str, tone: str) -> Dict[str, Any]:
    """Fallback template when Ollama is unavailable."""
    return {
        "draft_email": (
            f"Subject: Data Removal Request\n\n"
            f"Dear Site Administrator,\n\n"
            f"I am writing to request the removal of my personal information "
            f"that appears on your platform (reference: item {item_id}).\n\n"
            f"Under applicable data protection regulations, I have the right to "
            f"request deletion of my personal data. Please confirm within 30 days.\n\n"
            f"Thank you for your cooperation.\n"
            f"Best regards,\n[YOUR NAME]"
        ),
        "steps": [
            "Visit the website and locate the content containing your data.",
            "Look for a 'Contact Us' or 'Privacy' page to submit a removal request.",
            "If no response within 30 days, consider filing a complaint with your local data protection authority.",
        ],
        "settings_links": [],
    }