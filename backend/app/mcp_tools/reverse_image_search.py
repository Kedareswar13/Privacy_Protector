import os
from typing import List, Dict, Any


async def reverse_image_search(image_hash: str) -> List[Dict[str, Any]]:
    """Mock reverse image search.

    In MOCK_CONNECTORS mode, returns deterministic fake matches for the given
    image_hash. Later this can be wired to a real API like Bing Visual Search
    or TinEye. This performs image-level matching, *not* face recognition.
    """

    if os.getenv("MOCK_CONNECTORS", "false").lower() == "true":
        return [
            {
                "url": f"https://example.com/images/{image_hash}",
                "similarity": 0.95,
                "context": "Mock reverse image search result",
            }
        ]

    # TODO: Implement real reverse image search API integration.
    raise NotImplementedError("reverse_image_search not implemented for real mode")
