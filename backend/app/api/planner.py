from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from ..core import planner_service


router = APIRouter()


class PlannerRequest(BaseModel):
    state: Dict[str, Any]
    goal: str | None = "produce_risk_report"


@router.post("/plan")
async def get_plan(request: PlannerRequest) -> Dict[str, Any]:
    """Planner endpoint used for debugging and development.

    Accepts an arbitrary `state` object and an optional `goal`, and returns
    a JSON plan from the planner service.
    """

    plan = await planner_service.get_plan(state=request.state, goal=request.goal or "produce_risk_report")
    return plan
