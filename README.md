# Fake Job Detector

An AI-powered system to detect online job scams in real-time using URL analysis and provide ATS-friendly resume generation.

## Features

- **Job Fraud Detection**: Analyzes job postings using ML and LLM models
- **URL Analysis**: Extracts and processes content from job posting URLs
- **ATS-Friendly Resume Generation**: Creates optimized resumes for detected legitimate jobs
- **Multiple Export Formats**: Supports both PDF and DOCX resume formats
- **Modern Web Interface**: Clean, responsive UI with real-time feedback
- **User Authentication**: Secure user accounts with JWT authentication
- **Resume History**: Store and access previous job analyses and generated resumes

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)
- PostgreSQL database

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fake_job_detector
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database:
   - Create a database named `fake_job_detector`
   - Update the database credentials in the `.env` file

5. Set up environment variables:
Create a `.env` file in the root directory with:
```
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/fake_job_detector

# JWT Authentication
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

6. Run database migrations:
```bash
alembic upgrade head
```

## Running the Application

1. Make sure you're in the project root directory and your virtual environment is activated

2. Run the FastAPI application:
```bash
uvicorn app.main:app --reload
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Project Structure

```
fake_job_detector/
├── app/                    # Main application directory
│   ├── main.py            # FastAPI application
│   ├── auth.py            # Authentication logic
│   ├── database.py        # Database connection
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── routes/            # API routes
│   │   ├── auth.py        # Authentication routes
│   │   ├── job_analysis.py # Job analysis routes
│   │   └── resume.py      # Resume generation routes
│   ├── static/            # Static files (CSS, JS)
│   └── templates/         # HTML templates
├── data/                  # Data directory
├── migrations/            # Alembic migrations
├── models/                # Trained ML models
├── notebooks/            # Jupyter notebooks
├── scraper/              # Web scraper
├── tests/               # Test files
└── alembic.ini          # Alembic configuration
```

## API Documentation

After starting the application, you can access the interactive API documentation at:
```
http://localhost:8000/docs
```

## Usage

1. **Registration and Login**:
   - Create an account with your email and password
   - Log in to access the job analysis features

2. **Job Analysis**:
   - Enter a job posting URL
   - Click "Analyze" to get the fraud detection results
   - Review the detailed analysis and confidence score

3. **Resume Generation** (for legitimate jobs):
   - Fill in the resume form with your details
   - Add multiple entries for experience, education, and certifications
   - Choose your preferred format (PDF/DOCX)
   - Click "Generate & Download Resume"

4. **History**:
   - View your past job analyses 
   - Access and download previously generated resumes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 