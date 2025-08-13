from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional, List
from ..db import get_session
from ..models import Bundle, BundlePrompt, Prompt, User
from ..auth import get_current_user
from sqlalchemy import func

router = APIRouter(prefix="/api/bundles", tags=["bundles"])

class BundleCreate(BaseModel):
    title: str
    description: str
    price_cents: int
    prompt_ids: List[int]

class BundleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    is_active: Optional[bool] = None

@router.post("")
def create_bundle(data: BundleCreate, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Create a new prompt bundle"""
    # Validate price
    if data.price_cents <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than 0")
    
    # Verify all prompts exist and belong to user
    for prompt_id in data.prompt_ids:
        prompt = session.get(Prompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        if prompt.owner_id != user.id:
            raise HTTPException(status_code=403, detail=f"Prompt {prompt_id} does not belong to you")
    
    # Create bundle
    bundle = Bundle(
        name=data.title,
        description=data.description,
        price_cents=data.price_cents,
        owner_id=user.id
    )
    
    session.add(bundle)
    session.commit()
    session.refresh(bundle)
    
    # Add prompts to bundle
    for prompt_id in data.prompt_ids:
        bundle_prompt = BundlePrompt(bundle_id=bundle.id, prompt_id=prompt_id)
        session.add(bundle_prompt)
    
    session.commit()
    
    return {"id": bundle.id, "message": "Bundle created successfully"}

@router.get("")
def list_bundles(session: Session = Depends(get_session)):
    """List all active bundles"""
    bundles = session.exec(
        select(Bundle).where(Bundle.is_active == True)
    ).all()
    
    result = []
    for bundle in bundles:
        # Get prompt count
        prompt_count = session.exec(
            select(func.count(BundlePrompt.prompt_id))
            .where(BundlePrompt.bundle_id == bundle.id)
        ).first() or 0
        
        result.append({
            "id": bundle.id,
            "title": bundle.name,
            "description": bundle.description,
            "price_cents": bundle.price_cents,
            "price_formatted": f"${bundle.price_cents / 100:.2f}",
            "prompt_count": prompt_count,
            "created_at": bundle.created_at
        })
    
    return result

@router.get("/{bundle_id}")
def get_bundle(bundle_id: int, session: Session = Depends(get_session)):
    """Get bundle details with included prompts"""
    bundle = session.get(Bundle, bundle_id)
    if not bundle or not bundle.is_active:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Get prompts in bundle
    prompts = session.exec(
        select(Prompt)
        .join(BundlePrompt, Prompt.id == BundlePrompt.prompt_id)
        .where(BundlePrompt.bundle_id == bundle_id)
    ).all()
    
    prompt_list = []
    for prompt in prompts:
        prompt_list.append({
            "id": prompt.id,
            "title": prompt.title,
            "description": prompt.description,
            "price_cents": prompt.price_cents,
            "price_formatted": f"${prompt.price_cents / 100:.2f}"
        })
    
    return {
        "id": bundle.id,
        "title": bundle.name,
        "description": bundle.description,
        "price_cents": bundle.price_cents,
        "price_formatted": f"${bundle.price_cents / 100:.2f}",
        "prompts": prompt_list,
        "created_at": bundle.created_at
    }

@router.put("/{bundle_id}")
def update_bundle(bundle_id: int, data: BundleUpdate, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Update a bundle (owner only)"""
    bundle = session.get(Bundle, bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    if bundle.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only bundle owner can update")
    
    # Update fields
    if data.title is not None:
        bundle.name = data.title
    if data.description is not None:
        bundle.description = data.description
    if data.price_cents is not None:
        if data.price_cents <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than 0")
        bundle.price_cents = data.price_cents
    if data.is_active is not None:
        bundle.is_active = data.is_active
    
    session.commit()
    session.refresh(bundle)
    
    return {"message": "Bundle updated successfully"}

@router.delete("/{bundle_id}")
def delete_bundle(bundle_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Delete a bundle (owner only)"""
    bundle = session.get(Bundle, bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    if bundle.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only bundle owner can delete")
    
    # Delete bundle prompts first
    session.exec(
        select(BundlePrompt).where(BundlePrompt.bundle_id == bundle_id)
    ).delete()
    
    # Delete bundle
    session.delete(bundle)
    session.commit()
    
    return {"message": "Bundle deleted successfully"}

@router.get("/my-bundles")
def get_my_bundles(user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Get bundles created by the current user"""
    bundles = session.exec(
        select(Bundle).where(Bundle.owner_id == user.id)
    ).all()
    
    result = []
    for bundle in bundles:
        # Get prompt count
        prompt_count = session.exec(
            select(func.count(BundlePrompt.prompt_id))
            .where(BundlePrompt.bundle_id == bundle.id)
        ).first() or 0
        
        result.append({
            "id": bundle.id,
            "title": bundle.name,
            "description": bundle.description,
            "price_cents": bundle.price_cents,
            "price_formatted": f"${bundle.price_cents / 100:.2f}",
            "prompt_count": prompt_count,
            "is_active": bundle.is_active,
            "created_at": bundle.created_at
        })
    
    return result 