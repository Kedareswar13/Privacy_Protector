from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from ..db.session import get_session
from ..db.models import Consent
from ..core.auth_utils import get_current_user_id


router = APIRouter()


class ConsentRequest(BaseModel):
    scopes: Dict[str, Any]


@router.post("")
async def create_consent(payload: ConsentRequest, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)) -> Dict[str, Any]:
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    consent = Consent(user_id=user_id, scopes_json=payload.scopes.__repr__())
    session.add(consent)
    session.commit()
    session.refresh(consent)
    return {"consent_id": consent.id, "user_id": consent.user_id}
