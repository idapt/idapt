from contextlib import contextmanager
from typing import Generator, AsyncGenerator
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException
from sqlalchemy import create_engine
import logging
from app.database.connection import get_connection_string
from app.database.initialization.migration_manager import run_migrations

logger = logging.getLogger(__name__)

def create_session() -> Session:
    """Create a new database session"""

    # Run migrations and set up the database if needed
    run_migrations()

    engine = create_engine(
        get_connection_string(),
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # SQLite busy timeout in seconds
        }
    )
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    return SessionLocal()

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