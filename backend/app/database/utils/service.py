from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException
from sqlalchemy import create_engine
import logging
from app.database.utils.migration_manager import run_migrations
import os

logger = logging.getLogger("uvicorn")

def create_session(db_path: str, script_location: str, models_declarative_base_class) -> Session:
    """Create a new database session"""
    try:
        # Check if database file exists and create empty one if not
        if not os.path.exists(db_path):
            
            # Create folder for the database
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with open(db_path, 'w') as f:
                pass

        engine = create_engine(
            "sqlite:///" + db_path,
            connect_args={
                "check_same_thread": False,
                "timeout": 30  # SQLite busy timeout in seconds
            }
        )
        
        # Run migrations if needed
        run_migrations(engine, db_path, script_location, models_declarative_base_class)
        
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
def get_session(db_path: str, script_location: str, models_declarative_base_class) -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = create_session(db_path, script_location, models_declarative_base_class)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()