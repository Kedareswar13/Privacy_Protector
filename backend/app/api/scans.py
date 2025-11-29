from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db.session import get_session
from ..db.models import Scan, Item
from ..core.scan_runner import run_scan_once
from ..core.auth_utils import decode_token


router = APIRouter()


class Seeds(BaseModel):
    name: str | None = None
    email: str | None = None
    usernames: list[str] | None = None
    phones: list[str] | None = None


class CreateScanRequest(BaseModel):
    seeds: Seeds


@router.post("")
async def create_scan(
    payload: CreateScanRequest,
    session: Session = Depends(get_session),
    authorization: str | None = None,
) -> Dict[str, Any]:
    user_id = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        user_id = decode_token(token)

    scan = Scan(seeds_json=payload.seeds.json(), status="pending", user_id=user_id)
    session.add(scan)
    session.commit()
    session.refresh(scan)
    return {"scan_id": scan.id}


@router.get("/{scan_id}")
async def get_scan(scan_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    statement = select(Scan).where(Scan.id == scan_id)
    scan = session.exec(statement).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "seeds_json": scan.seeds_json,
        "created_at": scan.created_at,
        "updated_at": scan.updated_at,
    }


@router.post("/{scan_id}/run")
async def run_scan(scan_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    result = await run_scan_once(scan_id=scan_id, session=session)
    return result


@router.get("/{scan_id}/items")
async def list_scan_items(scan_id: int, session: Session = Depends(get_session)) -> List[Dict[str, Any]]:
    statement = select(Item).where(Item.scan_id == scan_id)
    items = session.exec(statement).all()
    return [
        {
            "id": item.id,
            "category": item.category,
            "source": item.source,
            "title": item.title,
            "snippet": item.snippet,
            "url": item.url,
            "confidence": item.confidence,
            "risk_score": item.risk_score,
        }
        for item in items
    ]


@router.get("/items/{item_id}")
async def get_item(item_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    statement = select(Item).where(Item.id == item_id)
    item = session.exec(statement).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": item.id,
        "scan_id": item.scan_id,
        "category": item.category,
        "source": item.source,
        "title": item.title,
        "snippet": item.snippet,
        "url": item.url,
        "confidence": item.confidence,
        "risk_score": item.risk_score,
        "metadata_json": item.metadata_json,
        "created_at": item.created_at,
    }
