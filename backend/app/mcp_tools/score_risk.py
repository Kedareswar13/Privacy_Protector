from typing import List, Dict, Any

async def score_risk(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for item in items:
        category = item.get("category", "unknown")
        confidence = item.get("confidence", 0.5)
        base_weights = {
            "breach": 0.40,
            "github_profile": 0.25,
            "web_result": 0.20,
            "image_match": 0.15,
            "unknown": 0.10
        }
        risk_score = base_weights.get(category, 0.10) * confidence
        results.append({
            "item_id": item.get("id"),
            "risk_score": risk_score,
            "category": category,
            "explanation": f"Category {category} with confidence {confidence}"
        })
    return results