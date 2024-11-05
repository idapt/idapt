import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .service import DatabaseService

def get_connection_string() -> str:
    """Get the database connection string from environment variables"""
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "defaultpassword")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "postgres")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

# Create global engine and session factory
engine = create_engine(get_connection_string())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create database service singleton
db_service = DatabaseService(SessionLocal)
get_db_session = db_service.get_db
