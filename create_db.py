import os
import logging
from dotenv import load_dotenv
import psycopg2
import sys
from app.database import engine, Base
from app.models import User, JobAnalysis, Resume, BlacklistedJob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment variables")

# Parse the SQLAlchemy URL to get components for psycopg2
url_parts = DATABASE_URL.replace("postgresql://", "").split("/")
dbname = url_parts[1]
user_host = url_parts[0].split("@")
if ":" in user_host[0]:
    user, password = user_host[0].split(":")
else:
    user = user_host[0]
    password = "goutham9"
host = user_host[1].split(":")[0] if "@" in DATABASE_URL else "localhost"
port = user_host[1].split(":")[1] if ":" in user_host[1] else "5432"

def create_database():
    try:
        # Connect to the default 'postgres' database to create our new database
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if the database already exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{dbname}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database: {dbname}")
            cursor.execute(f"CREATE DATABASE {dbname}")
            logger.info(f"Database {dbname} created successfully")
        else:
            logger.info(f"Database {dbname} already exists")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        return False

def run_alembic_migration():
    try:
        # Run alembic migrations
        logger.info("Running database migrations")
        os.system("alembic upgrade head")
        logger.info("Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        return False

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    logger.info("Initializing database")
    
    # Create database
    if create_database():
        # Run migrations
        if run_alembic_migration():
            logger.info("Database setup completed successfully")
            create_tables()
            print("Database tables created successfully!")
        else:
            logger.error("Database migrations failed")
    else:
        logger.error("Database creation failed") 