from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
import logging
from app.api.migration_manager import run_migrations
import os

logger = logging.getLogger("uvicorn")

@contextmanager
def get_session(db_path: str, script_location: str, models_declarative_base_class) -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    try:
        # Check if database file exists and create empty one if not
        if not os.path.exists(db_path):            
            # Create folder for the database
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with open(db_path, 'w') as f:
                pass

        connection_string = "sqlite:///" + db_path

        engine = create_engine(
            connection_string,
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
        session = SessionLocal()
        
        # Run migrations on the engine with a dedicated connection before making the engine avaliable
        with engine.begin() as connection:
            run_migrations(
                connection=connection,
                connection_string=connection_string,
                script_location=script_location,
                models_declarative_base_class=models_declarative_base_class
            )

        yield session

    finally:
        session.close()