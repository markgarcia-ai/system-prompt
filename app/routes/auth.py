from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from ..db import get_session
from ..models import User
from ..auth import hash_pw, verify_pw, create_token, get_current_user
from typing import Optional
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    paypal_email: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

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

@router.get("/me")
def get_profile(user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Get current user's profile"""
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "website": user.website,
        "location": user.location,
        "paypal_email": user.paypal_email,
        "balance_cents": user.balance_cents,
        "created_at": user.created_at
    }

@router.put("/profile")
def update_profile(data: ProfileUpdate, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Update user profile"""
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.bio is not None:
        user.bio = data.bio
    if data.website is not None:
        user.website = data.website
    if data.location is not None:
        user.location = data.location
    if data.paypal_email is not None:
        user.paypal_email = data.paypal_email
    
    session.commit()
    session.refresh(user)
    return {"message": "Profile updated successfully"}

@router.put("/password")
def update_password(data: PasswordUpdate, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Update user password"""
    if not verify_pw(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    user.password_hash = hash_pw(data.new_password)
    session.commit()
    return {"message": "Password updated successfully"}

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Upload user avatar"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if it doesn't exist
    upload_dir = "app/static/uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file with unique name
    file_extension = file.filename.split('.')[-1]
    filename = f"avatar_{user.id}.{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update user avatar URL
    user.avatar_url = f"/static/uploads/avatars/{filename}"
    session.commit()
    
    return {"avatar_url": user.avatar_url}
