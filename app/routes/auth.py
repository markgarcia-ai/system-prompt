from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from ..db import get_session
from ..models import User
from ..auth import hash_pw, verify_pw, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(data: RegisterIn, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(email=data.email, password_hash=hash_pw(data.password))
    session.add(u); session.commit(); session.refresh(u)
    return {"token": create_token(u.id), "email": u.email}

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(data: LoginIn, session: Session = Depends(get_session)):
    u = session.exec(select(User).where(User.email == data.email)).first()
    if not u or not verify_pw(data.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(u.id), "email": u.email}
