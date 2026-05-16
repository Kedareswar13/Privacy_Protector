import os
from typing import Dict, Any


async def check_breach(email: str) -> Dict[str, Any]:
    """Check if an email has appeared in known data breaches.

    Currently returns a stub response.  When HIBP_API_KEY is configured this
    can be wired to the real Have-I-Been-Pwned API.
    """
    if os.getenv("MOCK_CONNECTORS", "false").lower() == "true":
        return {
            "pwned": True,
            "breaches": [
                {"name": "MockBreach2023", "date": "2023-06-01", "details": "Mock breach details"}
            ]
        }

    # Gracefully return "not checked" when the HIBP key is missing,
    # instead of crashing the scan pipeline.
    hibp_key = os.getenv("HIBP_API_KEY")
    if not hibp_key:
        return {
            "pwned": False,
            "breaches": [],
        }

    # TODO: Implement real HIBP API call with hibp_key
    return {
        "pwned": False,
        "breaches": [],
    }