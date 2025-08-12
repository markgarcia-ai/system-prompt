from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, or_
from typing import Optional, List
from ..db import get_session
from ..models import Prompt, Tag, PromptTag, PromptOutput
from ..auth import get_current_user_optional

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("")
def search_prompts(
    q: Optional[str] = Query(None, description="Search query"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating"),
    max_price: Optional[int] = Query(None, description="Maximum price in cents"),
    license_type: Optional[str] = Query(None, description="License type filter"),
    featured: bool = Query(False, description="Show only featured prompts"),
    session: Session = Depends(get_session)
):
    """Search prompts with various filters"""
    query = select(Prompt).where(Prompt.is_active == True)
    
    # Text search
    if q:
        query = query.where(
            or_(
                Prompt.title.contains(q),
                Prompt.description.contains(q),
                Prompt.content.contains(q)
            )
        )
    
    # Tag filter
    if tag:
        query = query.join(PromptTag, Prompt.id == PromptTag.prompt_id)\
                    .join(Tag, PromptTag.tag_id == Tag.id)\
                    .where(Tag.name == tag)
    
    # Price filter
    if max_price:
        query = query.where(Prompt.price_cents <= max_price)
    
    # License filter
    if license_type:
        query = query.where(Prompt.license_type == license_type)
    
    # Featured filter
    if featured:
        query = query.where(Prompt.is_featured == True)
    
    prompts = session.exec(query.order_by(Prompt.created_at.desc())).all()
    
    # Get tags and stats for each prompt
    result = []
    for prompt in prompts:
        # Get tags
        prompt_tags = session.exec(
            select(Tag.name)
            .join(PromptTag, Tag.id == PromptTag.tag_id)
            .where(PromptTag.prompt_id == prompt.id)
        ).all()
        
        # Get average rating
        avg_rating = session.exec(
            select(func.avg(PromptOutput.rating))
            .where(PromptOutput.prompt_id == prompt.id, PromptOutput.rating.is_not(None))
        ).first()
        
        # Get total outputs
        total_outputs = session.exec(
            select(func.count(PromptOutput.id))
            .where(PromptOutput.prompt_id == prompt.id)
        ).first()
        
        result.append({
            "id": prompt.id,
            "title": prompt.title,
            "description": prompt.description,
            "price_cents": prompt.price_cents,
            "views": prompt.views,
            "license_type": prompt.license_type,
            "is_featured": prompt.is_featured,
            "tags": prompt_tags,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "total_outputs": total_outputs or 0,
            "price_formatted": f"${prompt.price_cents / 100:.2f}"
        })
    
    # Filter by minimum rating if specified
    if min_rating:
        result = [p for p in result if p["average_rating"] and p["average_rating"] >= min_rating]
    
    return result

@router.get("/recommendations")
def get_recommendations(
    user=Depends(get_current_user_optional),
    session: Session = Depends(get_session),
    limit: int = Query(6, description="Number of recommendations")
):
    """Get personalized recommendations based on user history"""
    if not user:
        # Return featured prompts for non-logged in users
        featured = session.exec(
            select(Prompt)
            .where(Prompt.is_active == True, Prompt.is_featured == True)
            .order_by(Prompt.views.desc())
            .limit(limit)
        ).all()
        
        return [{
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "price_cents": p.price_cents,
            "views": p.views,
            "license_type": p.license_type,
            "is_featured": p.is_featured,
            "price_formatted": f"${p.price_cents / 100:.2f}",
            "reason": "Featured"
        } for p in featured]
    
    # Get user's purchase history
    from ..models import Purchase
    user_purchases = session.exec(
        select(Purchase.prompt_id)
        .where(Purchase.user_id == user.id)
    ).all()
    
    if not user_purchases:
        # No purchases, return popular prompts
        popular = session.exec(
            select(Prompt)
            .where(Prompt.is_active == True)
            .order_by(Prompt.views.desc())
            .limit(limit)
        ).all()
        
        return [{
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "price_cents": p.price_cents,
            "views": p.views,
            "license_type": p.license_type,
            "is_featured": p.is_featured,
            "price_formatted": f"${p.price_cents / 100:.2f}",
            "reason": "Popular"
        } for p in popular]
    
    # Get tags from user's purchased prompts
    user_tags = session.exec(
        select(Tag.name)
        .join(PromptTag, Tag.id == PromptTag.tag_id)
        .where(PromptTag.prompt_id.in_(user_purchases))
    ).all()
    
    # Find prompts with similar tags that user hasn't purchased
    if user_tags:
        similar_prompts = session.exec(
            select(Prompt)
            .join(PromptTag, Prompt.id == PromptTag.prompt_id)
            .join(Tag, PromptTag.tag_id == Tag.id)
            .where(
                Prompt.is_active == True,
                Tag.name.in_(user_tags),
                ~Prompt.id.in_(user_purchases)
            )
            .order_by(Prompt.views.desc())
            .limit(limit)
        ).all()
        
        if similar_prompts:
            return [{
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "price_cents": p.price_cents,
                "views": p.views,
                "license_type": p.license_type,
                "is_featured": p.is_featured,
                "price_formatted": f"${p.price_cents / 100:.2f}",
                "reason": "Based on your interests"
            } for p in similar_prompts]
    
    # Fallback to popular prompts
    popular = session.exec(
        select(Prompt)
        .where(Prompt.is_active == True, ~Prompt.id.in_(user_purchases))
        .order_by(Prompt.views.desc())
        .limit(limit)
    ).all()
    
    return [{
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "price_cents": p.price_cents,
        "views": p.views,
        "license_type": p.license_type,
        "is_featured": p.is_featured,
        "price_formatted": f"${p.price_cents / 100:.2f}",
        "reason": "Popular"
    } for p in popular]

@router.get("/trending")
def get_trending_prompts(
    session: Session = Depends(get_session),
    limit: int = Query(10, description="Number of trending prompts")
):
    """Get trending prompts based on recent activity"""
    # Get prompts with recent outputs
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    trending = session.exec(
        select(Prompt, func.count(PromptOutput.id).label('recent_outputs'))
        .outerjoin(PromptOutput, Prompt.id == PromptOutput.prompt_id)
        .where(
            Prompt.is_active == True,
            or_(
                PromptOutput.created_at >= week_ago,
                PromptOutput.id.is_(None)
            )
        )
        .group_by(Prompt.id)
        .order_by(func.count(PromptOutput.id).desc(), Prompt.views.desc())
        .limit(limit)
    ).all()
    
    return [{
        "id": prompt.id,
        "title": prompt.title,
        "description": prompt.description,
        "price_cents": prompt.price_cents,
        "views": prompt.views,
        "license_type": prompt.license_type,
        "is_featured": prompt.is_featured,
        "recent_outputs": recent_outputs,
        "price_formatted": f"${prompt.price_cents / 100:.2f}"
    } for (prompt, recent_outputs) in trending] 