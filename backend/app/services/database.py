from contextlib import contextmanager
from pathlib import Path
from typing import Generator, AsyncGenerator
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException
from sqlalchemy import create_engine
import logging
from app.database.connection import get_connection_string, get_db_path
from app.database.migration_manager import run_migrations
import os

logger = logging.getLogger("uvicorn")

def create_session() -> Session:
    """Create a new database session"""
    try:
        # Check if database file exists and create empty one if not
        if not os.path.exists(get_db_path()):
            
            # Create folder for the database
            db_dir = Path(get_db_path()).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with open(get_db_path(), 'w') as f:
                pass

        engine = create_engine(
            get_connection_string(),
            connect_args={
                "check_same_thread": False,
                "timeout": 30  # SQLite busy timeout in seconds
            }
        )
        
        # Run migrations if needed
        run_migrations(engine)
        
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
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = create_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

async def get_db() -> AsyncGenerator[Session, None]:
    """FastAPI dependency for database sessions"""
    session = create_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

def get_db_session():
    with get_session() as session:
        yield session