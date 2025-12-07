from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import google.genai as genai
import os
from dotenv import load_dotenv
from typing import List
import joblib
import time
from contextlib import contextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app import schemas, models, auth
from app.database import get_db
from scraper.scraper import scrape_website

load_dotenv()

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load ML models
MODEL_DIR = os.path.join(BASE_DIR, "models")
sgd_classifier = joblib.load(os.path.join(MODEL_DIR, "sgd_classifier.joblib"))
count_vectorizer = joblib.load(os.path.join(MODEL_DIR, "count_vectorizer.joblib"))

# Get environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# client=genai.Client(api_key=GEMINI_API_KEY)

router = APIRouter(
    prefix="/jobs",
    tags=["Job Analysis"],
    responses={404: {"description": "Not found"}},
)

# LLM prompt for job analysis
JOB_ANALYSIS_PROMPT = """
You are a job posting expert. Analyze this job posting and validate the machine learning model's prediction.
Consider:
1. The job description, url and requirements
2. Company information
3. Any red flags or positive indicators
4. Salary and benefits information
5. Application process

Job URL: {url}
Job Content: {content}
ML Model Prediction: {prediction}
ML Model Confidence: {confidence}%

Provide a JSON response with the following structure:
{{
    "is_fake": boolean,
    "confidence": float (0-100),
    "reasoning": string,
    "original_prediction": boolean,
    "original_confidence": float
    
}}

Your response should be a valid JSON object only, no additional text.
"""

@contextmanager
def db_transaction(db: Session):
    try:
        yield
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=schemas.JobPrediction)
async def analyze_job(
    job_input: schemas.JobUrl,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Analyze a job posting and save the analysis to the database"""
    start_time = datetime.now()
    
    try:
        # Check if URL is in blacklist
        if job_input.url:
            blacklisted_job = db.query(models.BlacklistedJob).filter(
                models.BlacklistedJob.job_url == job_input.url
            ).first()
            
            if blacklisted_job:
                return schemas.JobPrediction(
                    id=0,  # Temporary ID for blacklisted jobs
                    job_analysis_id=0,
                    job_url=blacklisted_job.job_url,
                    job_title=blacklisted_job.job_title,
                    company_name=blacklisted_job.company_name,
                    is_fake=blacklisted_job.is_fake,
                    confidence=blacklisted_job.confidence,
                    reasoning=f"This job posting has been previously reported as fake by {blacklisted_job.report_count} users. {blacklisted_job.reasoning}",
                    processing_time=0,
                    is_blacklisted=True
                )
        
        # Get text from either URL or direct input
        if job_input.text:
            text = job_input.text
        else:
            if not job_input.url:
                raise HTTPException(
                    status_code=422,
                    detail="Either URL or text must be provided"
                )
            text = await scrape_website(str(job_input.url))
            print(f"web text:{text}")
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(
                status_code=422,
                detail="Insufficient job posting content. Text must be at least 50 characters long."
            )
        
        # Vectorize the text
        features = count_vectorizer.transform([text])
        
        # Get initial prediction and probability from SGD classifier
        original_is_fake = sgd_classifier.predict(features)[0]
        original_confidence = max(sgd_classifier.predict_proba(features)[0]) * 100
        
        # Get LLM validation
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = JOB_ANALYSIS_PROMPT.format(
                url=job_input.url or "Direct Text Input",
                content=text,
                prediction="fake" if original_is_fake else "legitimate",
                confidence=original_confidence
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': schemas.LLMValidationResponse,
                }
            )
            
            # Parse the LLM response
            llm_validation = response.parsed
            
            # Use LLM's validation if it's confident (confidence > 70%)
            if llm_validation.confidence > 70:
                is_fake = llm_validation.is_fake
                confidence = llm_validation.confidence
                reasoning = llm_validation.reasoning
            else:
                # Fall back to original prediction if LLM is uncertain
                is_fake = original_is_fake
                confidence = original_confidence
                reasoning = f"ML Model Prediction: {'Fake' if original_is_fake else 'Legitimate'} with {original_confidence:.2f}% confidence. LLM validation was uncertain."
                
        except Exception as e:
            # If LLM validation fails, use original prediction
            is_fake = original_is_fake
            confidence = original_confidence
            reasoning = f"ML Model Prediction: {'Fake' if original_is_fake else 'Legitimate'} with {original_confidence:.2f}% confidence. LLM validation failed: {str(e)}"
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Store job analysis in the database
        db_job_analysis = models.JobAnalysis(
            user_id=current_user.id,
            job_url=job_input.url or "Direct Text Input",
            is_fake=bool(is_fake),
            confidence=float(confidence),
            job_content=text,
            reasoning=reasoning
        )
        db.add(db_job_analysis)
        db.commit()
        db.refresh(db_job_analysis)
        
        # If job is fake and has a URL, add it to the blacklist
        if is_fake and job_input.url:
            blacklisted_job = db.query(models.BlacklistedJob).filter(
                models.BlacklistedJob.job_url == job_input.url
            ).first()
            
            if blacklisted_job:
                # Update existing blacklisted job
                blacklisted_job.report_count += 1
                blacklisted_job.confidence = max(blacklisted_job.confidence, confidence)
                blacklisted_job.reasoning = f"{blacklisted_job.reasoning}\n\nAdditional report: {reasoning}"
            else:
                # Create new blacklisted job entry
                blacklisted_job = models.BlacklistedJob(
                    job_url=job_input.url,
                    job_title=db_job_analysis.job_title,
                    company_name=db_job_analysis.company_name,
                    is_fake=True,
                    confidence=confidence,
                    reasoning=reasoning
                )
                db.add(blacklisted_job)
            
            db.commit()
        
        return schemas.JobPrediction(
            id=db_job_analysis.id,
            job_analysis_id=db_job_analysis.id,
            job_url=db_job_analysis.job_url,
            job_title=db_job_analysis.job_title,
            company_name=db_job_analysis.company_name,
            is_fake=db_job_analysis.is_fake,
            confidence=db_job_analysis.confidence,
            reasoning=db_job_analysis.reasoning,
            processing_time=processing_time,
            is_blacklisted=False
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing job: {str(e)}")


@router.get("/history", response_model=List[schemas.JobAnalysis])
@cache(expire=300)  # Cache for 5 minutes
async def get_job_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Get the job analysis history for the current user"""
    job_analyses = db.query(models.JobAnalysis).options(
        joinedload(models.JobAnalysis.resumes)
    ).filter(
        models.JobAnalysis.user_id == current_user.id
    ).order_by(models.JobAnalysis.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert the database models to Pydantic models
    return [
        schemas.JobAnalysis(
            id=job.id,
            user_id=job.user_id,
            job_url=job.job_url,
            job_title=job.job_title,
            company_name=job.company_name,
            is_fake=job.is_fake,
            confidence=job.confidence,
            job_content=job.job_content,
            reasoning=job.reasoning,
            created_at=job.created_at,
            resumes=[
                schemas.Resume(
                    id=resume.id,
                    user_id=resume.user_id,
                    job_analysis_id=resume.job_analysis_id,
                    format=resume.format,
                    file_path=resume.file_path,
                    created_at=resume.created_at
                ) for resume in job.resumes
            ]
        ) for job in job_analyses
    ]


@router.get("/{job_id}", response_model=schemas.JobAnalysis)
async def get_job_analysis(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Get a specific job analysis by ID"""
    job_analysis = db.query(models.JobAnalysis).filter(
        models.JobAnalysis.id == job_id,
        models.JobAnalysis.user_id == current_user.id
    ).first()
    
    if not job_analysis:
        raise HTTPException(status_code=404, detail="Job analysis not found")
    
    return job_analysis


@router.delete("/{job_analysis_id}", response_model=dict)
async def delete_job_analysis(
    job_analysis_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Delete a job analysis and its associated resumes.
    """
    # Get the job analysis from database
    job_analysis = db.query(models.JobAnalysis).filter(
        models.JobAnalysis.id == job_analysis_id,
        models.JobAnalysis.user_id == current_user.id
    ).first()
    
    if not job_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found"
        )
    
    try:
        # Delete associated resumes and their files
        for resume in job_analysis.resumes:
            if resume.file_path and os.path.exists(resume.file_path):
                os.remove(resume.file_path)
            db.delete(resume)
        
        # Delete the job analysis record
        db.delete(job_analysis)
        db.commit()
        
        return {"message": "Job analysis and associated resumes deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job analysis: {str(e)}"
        ) 