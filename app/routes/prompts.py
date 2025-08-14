from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Optional
from ..db import get_session
from ..models import Prompt, Purchase, Tag, PromptTag, PromptWatermark, Analytics
from ..auth import get_current_user

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

class PromptIn(BaseModel):
    title: str
    description: str
    content: str
    price_cents: int
    tags: Optional[List[str]] = []
    license_type: str = "personal"

@router.get("")
def list_prompts(
    session: Session = Depends(get_session),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    featured: bool = Query(False, description="Show only featured prompts")
):
    """List prompts with optional filtering"""
    query = select(Prompt).where(Prompt.is_active == True)
    
    if featured:
        query = query.where(Prompt.is_featured == True)
    
    if tag:
        # Filter by tag
        query = query.join(PromptTag, Prompt.id == PromptTag.prompt_id)\
                    .join(Tag, PromptTag.tag_id == Tag.id)\
                    .where(Tag.name == tag)
    
    prompts = session.exec(query.order_by(Prompt.created_at.desc())).all()
    
    # Get tags for each prompt
    result = []
    for prompt in prompts:
        prompt_tags = session.exec(
            select(Tag.name)
            .join(PromptTag, Tag.id == PromptTag.tag_id)
            .where(PromptTag.prompt_id == prompt.id)
        ).all()
        
        result.append({
            "id": prompt.id,
            "title": prompt.title,
            "description": prompt.description,
            "price_cents": prompt.price_cents,
            "views": prompt.views,
            "license_type": prompt.license_type,
            "is_featured": prompt.is_featured,
            "tags": prompt_tags,
            "price_formatted": f"${prompt.price_cents / 100:.2f}"
        })
    
    return result

@router.get("/{prompt_id}")
def get_prompt(prompt_id: int, session: Session = Depends(get_session)):
    """Get prompt details by ID (public)"""
    p = session.get(Prompt, prompt_id)
    if not p:
        raise HTTPException(status_code=404)

    p.views += 1

    # Track analytics event (only for logged-in users)
    # For anonymous views, we just increment the view count above
    session.commit()

    # Get tags for this prompt
    tags = session.exec(select(Tag).join(PromptTag).where(PromptTag.prompt_id == prompt_id)).all()
    
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "content": p.content,
        "preview": p.preview,
        "price": p.price,
        "price_formatted": f"${p.price:.2f}",
        "views": p.views,
        "downloads": p.downloads,
        "license_type": p.license_type,
        "is_featured": p.is_featured,
        "created_at": p.created_at,
        "tags": [{"id": tag.id, "name": tag.name} for tag in tags]
    }

@router.get("/{prompt_id}/ownership")
def check_prompt_ownership(prompt_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Check if current user owns this prompt"""
    p = session.get(Prompt, prompt_id)
    if not p:
        raise HTTPException(status_code=404)
    
    return {"owns_prompt": p.user_id == user.id}

@router.post("")
def create_prompt(data: PromptIn, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Create a new prompt with tags"""
    # Create the prompt
    prompt_data = data.dict(exclude={'tags'})
    p = Prompt(**prompt_data, owner_id=user.id)
    session.add(p)
    session.commit()
    session.refresh(p)
    
    # Add tags if provided
    if data.tags:
        for tag_name in data.tags:
            # Get or create tag
            tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
            if not tag:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.commit()
                session.refresh(tag)
            
            # Link tag to prompt
            prompt_tag = PromptTag(prompt_id=p.id, tag_id=tag.id)
            session.add(prompt_tag)
        
        session.commit()
    
    return {"id": p.id}

@router.get("/{prompt_id}/full")
def get_full_prompt(prompt_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Get full prompt content with watermarking for purchasers"""
    p = session.get(Prompt, prompt_id)
    if not p: 
        raise HTTPException(status_code=404)
    
    owns = (p.owner_id == user.id)
    bought = session.exec(select(Purchase).where(Purchase.user_id==user.id, Purchase.prompt_id==prompt_id)).first()
    
    if not (owns or bought): 
        raise HTTPException(status_code=403, detail="Purchase required")
    
    # Add watermark for buyers (not owners)
    content = p.content
    if bought and not owns:
        # Check if watermark already exists
        existing_watermark = session.exec(
            select(PromptWatermark).where(
                PromptWatermark.prompt_id == prompt_id,
                PromptWatermark.buyer_id == user.id
            )
        ).first()
        
        if not existing_watermark:
            # Create watermark token
            import uuid
            watermark_token = f"PM_{user.id}_{uuid.uuid4().hex[:8]}"
            
            # Insert invisible watermark into content
            # Using zero-width space and other invisible characters
            watermark = "\u200b" + watermark_token + "\u200b"
            content = content + watermark
            
            # Store watermark record
            watermark_record = PromptWatermark(
                prompt_id=prompt_id,
                buyer_id=user.id,
                token=watermark_token
            )
            session.add(watermark_record)
            session.commit()
        else:
            # Use existing watermark
            watermark = "\u200b" + existing_watermark.token + "\u200b"
            content = content + watermark
    
    return {"id": p.id, "content": content}

@router.get("/featured")
def get_featured_prompts(session: Session = Depends(get_session)):
    """Get featured prompts"""
    prompts = session.exec(
        select(Prompt)
        .where(Prompt.is_active == True, Prompt.is_featured == True)
        .order_by(Prompt.created_at.desc())
    ).all()
    
    result = []
    for prompt in prompts:
        prompt_tags = session.exec(
            select(Tag.name)
            .join(PromptTag, Tag.id == PromptTag.tag_id)
            .where(PromptTag.prompt_id == prompt.id)
        ).all()
        
        result.append({
            "id": prompt.id,
            "title": prompt.title,
            "description": prompt.description,
            "price_cents": prompt.price_cents,
            "views": prompt.views,
            "license_type": prompt.license_type,
            "tags": prompt_tags,
            "price_formatted": f"${prompt.price_cents / 100:.2f}"
        })
    
    return result
