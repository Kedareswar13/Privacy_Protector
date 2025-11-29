from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db.session import get_session
from ..db.models import Item
from ..mcp_tools import generate_remediation


router = APIRouter()


class ItemActionRequest(BaseModel):
    action: str
    tone: str | None = "polite"


@router.post("/{item_id}/action")
async def item_action(item_id: int, payload: ItemActionRequest, session: Session = Depends(get_session)) -> Dict[str, Any]:
    statement = select(Item).where(Item.id == item_id)
    item = session.exec(statement).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.action != "draft_email":
        raise HTTPException(status_code=400, detail="Unsupported action")

    result = await generate_remediation.generate_remediation(
        item_id=str(item.id),
        tone=payload.tone or "polite",
    )
    return result
