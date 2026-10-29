import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import the database and models
from app.database import engine, get_db, Base
from app import models
from app.routes import auth, job_analysis, resume
from app.api.endpoints import api_router
from app.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create the database tables
Base.metadata.create_all(bind=engine)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize the app
app = FastAPI(
    title="Fake Job Detector",
    description="API for detecting fraudulent job postings",
    version="1.0.0"
)

# Initialize FastAPI Cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

FastAPICache.init(InMemoryBackend())

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files with absolute paths
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(job_analysis.router)
app.include_router(resume.router)

# Add API routes
app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
    tags=["api"]
)

# Add backward compatibility routes
@app.post("/api/check")
async def legacy_check_job(request: Request):
    """Backward compatibility route - redirects to the new analyze endpoint"""
    return RedirectResponse(url="/jobs/analyze", status_code=307)

@app.post("/api/generate-resume")
async def legacy_generate_resume(request: Request):
    """Backward compatibility route - redirects to the new resume generation endpoint"""
    return RedirectResponse(url="/resumes/generate", status_code=307)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Run the application with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 