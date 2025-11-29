from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from ..db.session import get_session
from ..db.models import User
from ..core.auth_utils import hash_password, verify_password, create_access_token


router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> Dict[str, Any]:
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"user_id": user.id, "email": user.email}


@router.post("/login")
async def login(payload: LoginRequest, session: Session = Depends(get_session)) -> Dict[str, Any]:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user.id)  # type: ignore[arg-type]
    return {"access_token": token, "token_type": "bearer"}
