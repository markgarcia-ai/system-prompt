from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select, func
from typing import Optional
from ..db import get_session
from ..models import PromptOutput, Prompt, Purchase, User, Analytics
from ..auth import get_current_user

router = APIRouter(prefix="/api/outputs", tags=["outputs"])

class OutputCreate(BaseModel):
    prompt_id: int
    content: str
    output_type: str = "text"  # 'text' or 'image'
    rating: Optional[int] = None
    feedback: Optional[str] = None

class OutputUpdate(BaseModel):
    content: Optional[str] = None
    output_type: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None

@router.post("")
def create_output(data: OutputCreate, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Create a new prompt output (only for prompt owners or purchasers)"""
    # Check if user owns or has purchased the prompt
    prompt = session.get(Prompt, data.prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    owns = (prompt.owner_id == user.id)
    purchased = session.exec(
        select(Purchase).where(Purchase.user_id == user.id, Purchase.prompt_id == data.prompt_id)
    ).first()
    
    if not (owns or purchased):
        raise HTTPException(status_code=403, detail="Must own or purchase prompt to create outputs")
    
    # Validate rating
    if data.rating is not None and (data.rating < 1 or data.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    output = PromptOutput(
        prompt_id=data.prompt_id,
        user_id=user.id,
        content=data.content,
        output_type=data.output_type,
        rating=data.rating,
        feedback=data.feedback
    )
    
    session.add(output)
    
    # Track output analytics
    analytics = Analytics(
        prompt_id=data.prompt_id,
        event_type="output",
        user_id=user.id
    )
    session.add(analytics)
    
    session.commit()
    session.refresh(output)
    
    return {"id": output.id, "message": "Output created successfully"}

@router.get("/prompt/{prompt_id}")
def get_prompt_outputs(prompt_id: int, session: Session = Depends(get_session)):
    """Get all outputs for a specific prompt (public)"""
    outputs = session.exec(
        select(PromptOutput, User.email)
        .join(User, PromptOutput.user_id == User.id)
        .where(PromptOutput.prompt_id == prompt_id)
        .order_by(PromptOutput.created_at.desc())
    ).all()
    
    return [{
        "id": output.id,
        "content": output.content,
        "output_type": output.output_type,
        "rating": output.rating,
        "feedback": output.feedback,
        "user_email": email,
        "created_at": output.created_at
    } for (output, email) in outputs]

@router.get("/prompt/{prompt_id}/stats")
def get_prompt_stats(prompt_id: int, session: Session = Depends(get_session)):
    """Get statistics for a prompt"""
    # Get average rating
    avg_rating = session.exec(
        select(func.avg(PromptOutput.rating))
        .where(PromptOutput.prompt_id == prompt_id, PromptOutput.rating.is_not(None))
    ).first()
    
    # Get total outputs
    total_outputs = session.exec(
        select(func.count(PromptOutput.id))
        .where(PromptOutput.prompt_id == prompt_id)
    ).first()
    
    # Get rating distribution
    rating_counts = session.exec(
        select(PromptOutput.rating, func.count(PromptOutput.id))
        .where(PromptOutput.prompt_id == prompt_id, PromptOutput.rating.is_not(None))
        .group_by(PromptOutput.rating)
        .order_by(PromptOutput.rating)
    ).all()
    
    rating_distribution = {rating: count for rating, count in rating_counts}
    
    return {
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "total_outputs": total_outputs or 0,
        "rating_distribution": rating_distribution
    }

@router.put("/{output_id}")
def update_output(output_id: int, data: OutputUpdate, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Update an output (only by the creator)"""
    output = session.get(PromptOutput, output_id)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    if output.user_id != user.id:
        raise HTTPException(status_code=403, detail="Can only update your own outputs")
    
    # Validate rating
    if data.rating is not None and (data.rating < 1 or data.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    if data.rating is not None:
        output.rating = data.rating
    if data.feedback is not None:
        output.feedback = data.feedback
    if data.content is not None:
        output.content = data.content
    if data.output_type is not None:
        output.output_type = data.output_type
    
    session.commit()
    session.refresh(output)
    
    return {"message": "Output updated successfully"}

@router.delete("/{output_id}")
def delete_output(output_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Delete an output (only by the creator)"""
    output = session.get(PromptOutput, output_id)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    if output.user_id != user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own outputs")
    
    session.delete(output)
    session.commit()
    
    return {"message": "Output deleted successfully"} 