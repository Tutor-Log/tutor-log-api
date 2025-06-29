from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from os import environ
import models

# Database configuration
DATABASE_URL = environ["DATABASE_URL"]

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session
