from pydantic import BaseModel, HttpUrl, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import field_validator


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Job URL schema
class JobUrl(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    useBrowser: bool = False

    @field_validator('url')
    def validate_url(cls, v, info):
        if not v and not info.data.get('text'):
            raise ValueError('Either URL or text must be provided')
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @field_validator('text')
    def validate_text(cls, v, info):
        if not v and not info.data.get('url'):
            raise ValueError('Either URL or text must be provided')
        if v and len(v.strip()) < 50:
            raise ValueError('Job posting text must be at least 50 characters long')
        return v

    class Config:
        extra = 'allow'  # Allow extra fields in the request


# Job Prediction schema
class JobPrediction(BaseModel):
    id: int
    job_analysis_id: int
    job_url: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    is_fake: bool
    confidence: float
    reasoning: str
    processing_time: float
    is_blacklisted: bool = False

    class Config:
        from_attributes = True


class LLMValidationResponse(BaseModel):
    is_fake: bool
    confidence: float
    reasoning: str
    original_prediction: bool
    original_confidence: float

    class Config:
        from_attributes = True


# Resume schemas
class ExperienceItem(BaseModel):
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    startDate: str = Field(..., description="Start date (MM/YYYY format)")
    endDate: Optional[str] = Field(None, description="End date (MM/YYYY format) or leave empty if current")
    current: Optional[bool] = Field(False, description="Whether this is the current position")
    description: str = Field(..., description="Job responsibilities and achievements in bullet points")


class EducationItem(BaseModel):
    institution: str = Field(..., description="Name of educational institution")
    degree: str = Field(..., description="Degree name")
    field: str = Field(..., description="Field of study")
    graduationDate: str = Field(..., description="Graduation date (MM/YYYY format)")


class CertificationItem(BaseModel):
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuing organization")


class ProjectItem(BaseModel):
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description and achievements")
    technologies: List[str] = Field(..., description="Technologies used in the project")
    startDate: str = Field(..., description="Start date (MM/YYYY format)")
    endDate: Optional[str] = Field(None, description="End date (MM/YYYY format) or leave empty if ongoing")
    current: Optional[bool] = Field(False, description="Whether this is an ongoing project")
    url: Optional[str] = Field(None, description="Project URL or repository link (optional)")


class ResumeBase(BaseModel):
    fullName: str = Field(..., description="Full name of the candidate")
    title: str = Field(..., description="Professional title")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    location: str = Field(..., description="Location (City, State)")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL (optional)")
    summary: str = Field(..., description="Professional summary tailored to the job")
    skills: List[str] = Field(..., description="List of relevant skills for the job")
    experience: List[ExperienceItem] = Field(..., description="Work experience entries")
    education: List[EducationItem] = Field(..., description="Education history")
    certifications: Optional[List[CertificationItem]] = Field(None, description="Certifications (if any)")
    projects: Optional[List[ProjectItem]] = Field(None, description="Personal or professional projects")


class ResumeRequest(BaseModel):
    job_details: str
    personal_info: dict
    format: str = "pdf"  # pdf or docx
    template: str = "modern"  # modern or classic


class ResumeCreate(BaseModel):
    job_analysis_id: int
    format: str


class Resume(BaseModel):
    id: str
    user_id: str
    job_analysis_id: int
    format: str
    file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Job Analysis Schema
class JobAnalysisCreate(BaseModel):
    job_url: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    is_fake: bool
    confidence: float
    job_content: str
    reasoning: str


class JobAnalysis(JobAnalysisCreate):
    id: int
    user_id: str
    created_at: datetime
    resumes: List[Resume] = []

    class Config:
        from_attributes = True


class CertificationInfo(BaseModel):
    name: str
    issuer: str


class ExperienceInfo(BaseModel):
    company: str
    title: str
    startDate: str
    endDate: Optional[str] = None
    current: Optional[bool] = False
    description: str


class EducationInfo(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    graduationDate: str


class PersonalInfo(BaseModel):
    fullName: str
    title: str
    email: str
    phone: str
    location: str
    linkedin: Optional[str] = None
    summary: str
    skills: List[str]
    experience: List[ExperienceInfo]
    education: List[EducationInfo]
    certifications: Optional[List[CertificationInfo]] = None


class ResumeGenerationRequest(BaseModel):
    personal_info: PersonalInfo
    format: str = "pdf"  # pdf or docx


class ResumeResponse(BaseModel):
    id: str
    message: str 