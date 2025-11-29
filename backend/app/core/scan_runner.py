import json
from typing import Any, Dict, List

from sqlmodel import Session, select

from ..db.models import Scan, Item, ToolCall
from ..mcp_tools import search_web, search_social, check_breach, score_risk, reverse_image_search
from . import planner_service


async def run_scan_once(scan_id: int, session: Session) -> Dict[str, Any]:
    """Run a single planner+tool iteration for the given scan.

    This is a mock implementation: it calls the planner once and executes
    only a subset of tools, storing Items and ToolCalls.
    """

    scan = session.exec(select(Scan).where(Scan.id == scan_id)).first()
    if not scan:
        raise ValueError("Scan not found")

    seeds = json.loads(scan.seeds_json)
    state = {
        "seeds": seeds,
        "items": [],
        "tool_calls": [],
    }

    plan = await planner_service.get_plan(state=state, goal="produce_risk_report")
    actions: List[Dict[str, Any]] = plan.get("actions", [])

    created_items: List[Item] = []

    for action in actions:
        tool = action.get("tool")
        args = action.get("args", {})

        if tool == "searchWeb":
            results = await search_web.search_web(**args)
            for r in results:
                item = Item(
                    scan_id=scan.id,
                    category="web_result",
                    source="web",
                    title=r.get("title", ""),
                    snippet=r.get("snippet", ""),
                    url=r.get("url", ""),
                    confidence=0.7,
                    risk_score=0.0,
                    metadata_json=json.dumps(r),
                )
                session.add(item)
                created_items.append(item)
            _log_tool_call(session, scan.id, tool, args, results)
        elif tool == "searchSocial":
            results = await search_social.search_social(**args)
            for r in results:
                item = Item(
                    scan_id=scan.id,
                    category="social_post",
                    source=args.get("service", "social"),
                    title=r.get("text", ""),
                    snippet=r.get("text", ""),
                    url=r.get("url", ""),
                    confidence=0.7,
                    risk_score=0.0,
                    metadata_json=json.dumps(r),
                )
                session.add(item)
                created_items.append(item)
            _log_tool_call(session, scan.id, tool, args, results)
        elif tool == "checkBreach":
            result = await check_breach.check_breach(**args)
            breaches = result.get("breaches", [])
            for b in breaches:
                item = Item(
                    scan_id=scan.id,
                    category="breach",
                    source="hibp",
                    title=b.get("name", "Breach"),
                    snippet=b.get("details", ""),
                    url=b.get("url", ""),
                    confidence=0.9,
                    risk_score=0.0,
                    metadata_json=json.dumps(b),
                )
                session.add(item)
                created_items.append(item)
            _log_tool_call(session, scan.id, tool, args, result)
        elif tool == "reverseImageSearch":
            results = await reverse_image_search.reverse_image_search(**args)
            for r in results:
                item = Item(
                    scan_id=scan.id,
                    category="image_match",
                    source="reverse_image",
                    title=r.get("url", "Image match"),
                    snippet=r.get("context", ""),
                    url=r.get("url", ""),
                    confidence=float(r.get("similarity", 0.0)),
                    risk_score=0.0,
                    metadata_json=json.dumps(r),
                )
                session.add(item)
                created_items.append(item)
            _log_tool_call(session, scan.id, tool, args, results)
        else:
            # For now, ignore other tools in the plan
            continue

    # Risk scoring for created items
    if created_items:
        # Ensure items have primary keys assigned
        session.flush()
        items_payload = [
            {
                "id": str(item.id),
                "category": item.category,
                "confidence": item.confidence,
            }
            for item in created_items
        ]
        scores = await score_risk.score_risk(items_payload)
        by_id = {s.get("item_id"): s for s in scores}
        for item in created_items:
            s = by_id.get(str(item.id))
            if s is not None:
                item.risk_score = float(s.get("risk_score", 0.0))

    scan.status = "completed"
    session.commit()

    return {
        "scan_id": scan.id,
        "status": scan.status,
        "items_created": len(created_items),
    }


def _log_tool_call(session: Session, scan_id: int, tool: str, args: Dict[str, Any], response: Any) -> None:
    call = ToolCall(
        scan_id=scan_id,
        tool_name=tool,
        args_json=json.dumps(args),
        response_json=json.dumps(response),
    )
    session.add(call)
