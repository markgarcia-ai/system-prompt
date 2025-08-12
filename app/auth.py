import os, bcrypt, datetime
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from .models import User
from .db import get_session

SECRET = os.getenv("JWT_SECRET", "devsecret")
ALGO = "HS256"
bearer = HTTPBearer()

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)}
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer), session: Session = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token.credentials, SECRET, algorithms=[ALGO])
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_user_optional(token: HTTPAuthorizationCredentials = Depends(bearer), session: Session = Depends(get_session)):
    """Get current user if authenticated, otherwise return None"""
    try:
        payload = jwt.decode(token.credentials, SECRET, algorithms=[ALGO])
        uid = int(payload["sub"])
    except Exception:
        return None
    user = session.get(User, uid)
    return user
