from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from ..db import get_session
from ..models import Prompt, Purchase, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/my-prompts")
def get_my_prompts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get prompts owned by the current user"""
    prompts = session.exec(
        select(Prompt).where(Prompt.owner_id == current_user.id)
    ).all()
    
    return [
        {
            "id": p.id,
            "title": p.title,
            "price_cents": p.price_cents,
            "views": p.views,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "price_formatted": f"${p.price_cents / 100:.2f}"
        }
        for p in prompts
    ]

@router.get("/my-purchases")
def get_my_purchases(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get purchases made by the current user"""
    purchases = session.exec(
        select(Purchase).where(Purchase.user_id == current_user.id)
    ).all()
    
    return [
        {
            "id": p.id,
            "prompt_id": p.prompt_id,
            "payment_id": p.payment_id,
            "created_at": p.created_at
        }
        for p in purchases
    ]

@router.get("/earnings")
def get_earnings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get earnings for the current user (seller only)"""
    if not current_user.is_seller:
        raise HTTPException(status_code=403, detail="Seller access required")
    
    # Get all purchases of prompts owned by this user
    purchases = session.exec(
        select(Purchase)
        .join(Prompt, Purchase.prompt_id == Prompt.id)
        .where(Prompt.owner_id == current_user.id)
    ).all()
    
    total_earnings = sum(
        session.get(Prompt, p.prompt_id).price_cents 
        for p in purchases
    )
    
    return {
        "total_earnings_cents": total_earnings,
        "total_earnings_formatted": f"${total_earnings / 100:.2f}",
        "total_sales": len(purchases)
    } 