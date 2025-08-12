from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, func
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
from ..db import get_session
from ..models import Analytics, Prompt, User, PromptOutput, Purchase
from ..auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

class AnalyticsEvent(BaseModel):
    prompt_id: int
    event_type: str  # view, purchase, output, rating
    event_data: Optional[Dict[str, Any]] = None

@router.post("/track")
def track_event(data: AnalyticsEvent, user=Depends(get_current_user_optional), session: Session = Depends(get_session)):
    """Track an analytics event"""
    # Verify prompt exists
    prompt = session.get(Prompt, data.prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Create analytics record
    analytics = Analytics(
        prompt_id=data.prompt_id,
        event_type=data.event_type,
        user_id=user.id if user else None,
        event_data=json.dumps(data.event_data) if data.event_data else None
    )
    
    session.add(analytics)
    session.commit()
    
    return {"message": "Event tracked successfully"}

@router.get("/prompt/{prompt_id}")
def get_prompt_analytics(
    prompt_id: int,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get analytics for a specific prompt (owner only)"""
    prompt = session.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only prompt owner can view analytics")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get event counts by type
    event_counts = session.exec(
        select(Analytics.event_type, func.count(Analytics.id))
        .where(
            Analytics.prompt_id == prompt_id,
            Analytics.created_at >= start_date
        )
        .group_by(Analytics.event_type)
    ).all()
    
    # Get daily views
    daily_views = session.exec(
        select(
            func.date(Analytics.created_at).label('date'),
            func.count(Analytics.id).label('count')
        )
        .where(
            Analytics.prompt_id == prompt_id,
            Analytics.event_type == 'view',
            Analytics.created_at >= start_date
        )
        .group_by(func.date(Analytics.created_at))
        .order_by(func.date(Analytics.created_at))
    ).all()
    
    # Get conversion metrics
    total_views = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.prompt_id == prompt_id,
            Analytics.event_type == 'view',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    total_purchases = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.prompt_id == prompt_id,
            Analytics.event_type == 'purchase',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    total_outputs = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.prompt_id == prompt_id,
            Analytics.event_type == 'output',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    # Calculate conversion rates
    view_to_purchase_rate = (total_purchases / total_views * 100) if total_views > 0 else 0
    purchase_to_output_rate = (total_outputs / total_purchases * 100) if total_purchases > 0 else 0
    
    return {
        "prompt_id": prompt_id,
        "period_days": days,
        "event_counts": dict(event_counts),
        "daily_views": [{"date": str(date), "count": count} for date, count in daily_views],
        "conversion_metrics": {
            "total_views": total_views,
            "total_purchases": total_purchases,
            "total_outputs": total_outputs,
            "view_to_purchase_rate": round(view_to_purchase_rate, 2),
            "purchase_to_output_rate": round(purchase_to_output_rate, 2)
        }
    }

@router.get("/dashboard")
def get_user_analytics(
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get analytics dashboard for user's prompts"""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get user's prompts
    user_prompts = session.exec(
        select(Prompt).where(Prompt.owner_id == user.id)
    ).all()
    
    prompt_ids = [p.id for p in user_prompts]
    
    if not prompt_ids:
        return {
            "total_prompts": 0,
            "total_views": 0,
            "total_purchases": 0,
            "total_revenue": 0,
            "top_performing_prompts": [],
            "recent_activity": []
        }
    
    # Get total views and purchases
    total_views = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.prompt_id.in_(prompt_ids),
            Analytics.event_type == 'view',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    total_purchases = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.prompt_id.in_(prompt_ids),
            Analytics.event_type == 'purchase',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    # Calculate revenue (90% of prompt prices)
    total_revenue = 0
    for prompt in user_prompts:
        purchases = session.exec(
            select(func.count(Analytics.id))
            .where(
                Analytics.prompt_id == prompt.id,
                Analytics.event_type == 'purchase',
                Analytics.created_at >= start_date
            )
        ).first() or 0
        total_revenue += (prompt.price_cents * purchases * 0.9) / 100  # Convert to dollars
    
    # Get top performing prompts
    prompt_performance = []
    for prompt in user_prompts:
        views = session.exec(
            select(func.count(Analytics.id))
            .where(
                Analytics.prompt_id == prompt.id,
                Analytics.event_type == 'view',
                Analytics.created_at >= start_date
            )
        ).first() or 0
        
        purchases = session.exec(
            select(func.count(Analytics.id))
            .where(
                Analytics.prompt_id == prompt.id,
                Analytics.event_type == 'purchase',
                Analytics.created_at >= start_date
            )
        ).first() or 0
        
        prompt_performance.append({
            "id": prompt.id,
            "title": prompt.title,
            "views": views,
            "purchases": purchases,
            "revenue": (prompt.price_cents * purchases * 0.9) / 100
        })
    
    # Sort by revenue
    prompt_performance.sort(key=lambda x: x["revenue"], reverse=True)
    top_performing = prompt_performance[:5]
    
    # Get recent activity
    recent_activity = session.exec(
        select(Analytics, Prompt.title)
        .join(Prompt, Analytics.prompt_id == Prompt.id)
        .where(
            Analytics.prompt_id.in_(prompt_ids),
            Analytics.created_at >= start_date
        )
        .order_by(Analytics.created_at.desc())
        .limit(10)
    ).all()
    
    activity_list = []
    for analytics, title in recent_activity:
        activity_list.append({
            "prompt_id": analytics.prompt_id,
            "prompt_title": title,
            "event_type": analytics.event_type,
            "created_at": analytics.created_at
        })
    
    return {
        "total_prompts": len(user_prompts),
        "total_views": total_views,
        "total_purchases": total_purchases,
        "total_revenue": round(total_revenue, 2),
        "top_performing_prompts": top_performing,
        "recent_activity": activity_list
    }

@router.get("/marketplace")
def get_marketplace_analytics(
    session: Session = Depends(get_session),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get marketplace-wide analytics (public)"""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get total prompts
    total_prompts = session.exec(select(func.count(Prompt.id))).first() or 0
    
    # Get total views
    total_views = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.event_type == 'view',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    # Get total purchases
    total_purchases = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.event_type == 'purchase',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    # Get total outputs
    total_outputs = session.exec(
        select(func.count(Analytics.id))
        .where(
            Analytics.event_type == 'output',
            Analytics.created_at >= start_date
        )
    ).first() or 0
    
    # Get trending prompts (most viewed in period)
    trending_prompts = session.exec(
        select(Prompt.title, func.count(Analytics.id).label('views'))
        .join(Analytics, Prompt.id == Analytics.prompt_id)
        .where(
            Analytics.event_type == 'view',
            Analytics.created_at >= start_date
        )
        .group_by(Prompt.id, Prompt.title)
        .order_by(func.count(Analytics.id).desc())
        .limit(5)
    ).all()
    
    return {
        "period_days": days,
        "total_prompts": total_prompts,
        "total_views": total_views,
        "total_purchases": total_purchases,
        "total_outputs": total_outputs,
        "trending_prompts": [{"title": title, "views": views} for title, views in trending_prompts]
    } 