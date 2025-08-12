from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import os
import uuid
from pathlib import Path
from typing import Optional
from ..auth import get_current_user

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("app/static/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Upload an image for prompt outputs"""
    
    # Validate file type
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Return the URL
    image_url = f"/static/uploads/{unique_filename}"
    
    return {
        "url": image_url,
        "filename": unique_filename,
        "message": "Image uploaded successfully"
    }

@router.get("/image/{filename}")
async def get_image(filename: str):
    """Serve uploaded images"""
    file_path = UPLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path) 