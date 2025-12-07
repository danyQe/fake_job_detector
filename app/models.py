from sqlalchemy import Boolean, Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from uuid import uuid4
from datetime import datetime


def generate_uuid():
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    job_analyses = relationship("JobAnalysis", back_populates="user")
    resumes = relationship("Resume", back_populates="user")


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    job_url = Column(String)
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    is_fake = Column(Boolean)
    confidence = Column(Float)
    job_content = Column(Text)
    reasoning = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="job_analyses")
    resumes = relationship("Resume", back_populates="job_analysis")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    job_analysis_id = Column(Integer, ForeignKey("job_analyses.id"))
    file_path = Column(String)
    format = Column(String)  # pdf or docx
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resumes")
    job_analysis = relationship("JobAnalysis", back_populates="resumes")
    
    @classmethod
    def get_compatible_columns(cls):
        """Return only the columns that exist in the current database schema."""
        # This helper function allows us to query only columns that exist in the database
        return [
            cls.id,
            cls.user_id,
            cls.job_analysis_id,
            cls.file_path,
            cls.format,
            cls.created_at
        ]


class BlacklistedJob(Base):
    __tablename__ = "blacklisted_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_url = Column(String, unique=True, index=True)
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    is_fake = Column(Boolean)
    confidence = Column(Float)
    reasoning = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    report_count = Column(Integer, default=1)  # Number of times this job has been reported as fake 