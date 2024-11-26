import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.database.initialization.password_manager import DatabasePasswordManager
def get_connection_string() -> str:
    """Get the database connection string from environment variables"""
    user = os.getenv("POSTGRES_USER", "postgres")
    # Get the database password from the password manager
    password_manager = DatabasePasswordManager()
    password = password_manager.read_stored_password()
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB", "postgres")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

# Create engine
sync_engine = create_engine(get_connection_string())

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@contextmanager
def get_db():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

async def get_db_session():
    """FastAPI dependency for database sessions"""
    with get_db() as session:
        yield session

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async def get_async_db_session() -> AsyncSession:
    async_engine = create_async_engine(
        get_connection_string(),
        echo=True,
    )
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session