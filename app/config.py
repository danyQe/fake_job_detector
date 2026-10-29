import os
from pathlib import Path
from typing import Optional

class Settings:
    # Base directory for the application
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    # Static file directory
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    
    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # OpenAI API settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # Email settings (for future use)
    MAIL_USERNAME: Optional[str] = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: Optional[str] = os.getenv("MAIL_FROM")
    MAIL_PORT: Optional[int] = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: Optional[str] = os.getenv("MAIL_SERVER")
    MAIL_TLS: bool = os.getenv("MAIL_TLS", "True").lower() == "true"
    MAIL_SSL: bool = os.getenv("MAIL_SSL", "False").lower() == "true"

    # Create necessary directories
    def __init__(self):
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.STATIC_DIR / "resumes", exist_ok=True)

# Instantiate settings object
settings = Settings() 