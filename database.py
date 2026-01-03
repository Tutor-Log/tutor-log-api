from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from os import environ

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = environ.get("POSTGRESQLCONNSTR_TUTORLOG")
if not DATABASE_URL:
    raise ValueError("POSTGRESQLCONNSTR_TUTORLOG environment variable is not set")
SKIP_DATABASE_SETUP = environ.get("SKIP_DATABASE_SETUP", "false").lower() == "true"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Create database tables"""
    if (SKIP_DATABASE_SETUP):
        print("Skipping database setup")
        return
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session
