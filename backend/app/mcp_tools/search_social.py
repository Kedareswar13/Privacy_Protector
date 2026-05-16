import os
from typing import List, Dict, Any


async def search_social(service: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search a social platform for mentions of the query.

    Currently only mock mode is fully implemented.  When the real API keys
    (GITHUB_TOKEN, etc.) are configured, this can be wired up.  In the
    meantime, returns an empty list instead of crashing.
    """
    if os.getenv("MOCK_CONNECTORS", "false").lower() == "true":
        return [
            {
                "id": f"mock-{service}-1",
                "text": f"Mock post from {service} about {query}",
                "url": f"https://{service}.com/mock/{query}",
                "timestamp": "2024-01-01T12:00:00Z",
                "meta": {"author": "mock_user"}
            }
        ]

    # Gracefully return empty list when a service isn't implemented yet,
    # so the scan pipeline doesn't crash.
    return []