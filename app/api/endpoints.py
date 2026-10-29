from fastapi import APIRouter, Query, Body, Depends, HTTPException
from fastapi.responses import  FileResponse
import os
from sqlalchemy.orm import Session
from app.services.resume_service import ResumeService
from app.models import Resume, User, JobAnalysis
from app.utils import get_current_active_user, get_db
from app import schemas

api_router = APIRouter()

@api_router.post("/resume/generate", response_model=schemas.ResumeResponse)
async def generate_resume(
    job_id: int = Query(..., description="Job analysis ID to tailor resume for"),
    resume_data: schemas.ResumeGenerationRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a tailored resume based on job analysis and user information
    """
    # Verify job analysis exists and belongs to user
    job = db.query(JobAnalysis).filter(
        JobAnalysis.id == job_id,
        JobAnalysis.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job analysis not found or not authorized to access"
        )
    
    # Process personal info and job details for LLM
    job_details = {
        "title": job.job_title,
        "description": job.job_content,
        "company": job.company_name,
        "analysis": {
            "is_fake": job.is_fake,
            "confidence": job.confidence,
            "reasoning": job.reasoning
        }
    }
    
    # Generate resume using the resume service
    resume_service = ResumeService(db)
    resume_id = await resume_service.generate_resume(
        user_id=current_user.id,
        job_details=job_details,
        personal_info=resume_data.personal_info,
        format=resume_data.format
    )
    
    if not resume_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate resume"
        )
    
    return {"id": resume_id, "message": "Resume generated successfully"}

@api_router.get("/resumes/download/{resume_id}")
async def download_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download a generated resume
    """
    # Verify resume exists and belongs to user
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found or not authorized to access"
        )
    
    # Check if file exists
    file_path = resume.file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Resume file not found"
        )
    
    # Determine filename and content type
    filename = os.path.basename(file_path)
    content_type = "application/pdf"
    if file_path.endswith(".docx"):
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=content_type
    ) 