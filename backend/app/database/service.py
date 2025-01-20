from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException
from sqlalchemy import create_engine
import logging
from app.database.migration_manager import run_migrations
import os

from app.database.utils import get_db_path, get_connection_string

logger = logging.getLogger("uvicorn")

def create_session(user_id: str) -> Session:
    """Create a new database session"""
    try:
        # Check if database file exists and create empty one if not
        if not os.path.exists(get_db_path(user_id)):
            
            # Create folder for the database
            db_dir = Path(get_db_path(user_id)).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with open(get_db_path(user_id), 'w') as f:
                pass

        engine = create_engine(
            get_connection_string(user_id),
            connect_args={
                "check_same_thread": False,
                "timeout": 30  # SQLite busy timeout in seconds
            }
        )
        
        # Run migrations if needed
        run_migrations(engine, user_id)
        
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        return SessionLocal()
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@contextmanager
def get_session(user_id: str) -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = create_session(user_id)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

def get_db_session(user_id: str):
    with get_session(user_id) as session:
        yield session
