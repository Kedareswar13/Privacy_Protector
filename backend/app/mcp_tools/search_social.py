import os
from typing import List, Dict, Any

async def search_social(service: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
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
    # TODO: Implement GitHub/Reddit API calls
    raise NotImplementedError(f"{service} search not implemented")