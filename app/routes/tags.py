from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models import Tag, PromptTag, Prompt
from ..auth import get_current_user

router = APIRouter(prefix="/api/tags", tags=["tags"])

@router.get("")
def list_tags(session: Session = Depends(get_session)):
    """Get all available tags"""
    tags = session.exec(select(Tag).order_by(Tag.name)).all()
    return [{"id": tag.id, "name": tag.name} for tag in tags]

@router.get("/popular")
def get_popular_tags(session: Session = Depends(get_session), limit: int = 10):
    """Get most popular tags based on usage"""
    # Count tag usage
    tag_counts = session.exec(
        select(Tag.name, Tag.id)
        .join(PromptTag, Tag.id == PromptTag.tag_id)
        .group_by(Tag.id, Tag.name)
        .order_by(select(PromptTag.tag_id).count().desc())
        .limit(limit)
    ).all()
    
    return [{"id": tag_id, "name": name} for name, tag_id in tag_counts]

@router.post("")
def create_tag(name: str, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Create a new tag (admin only for now)"""
    # Check if tag already exists
    existing_tag = session.exec(select(Tag).where(Tag.name == name)).first()
    if existing_tag:
        return {"id": existing_tag.id, "name": existing_tag.name}
    
    # Create new tag
    tag = Tag(name=name)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    
    return {"id": tag.id, "name": tag.name} 