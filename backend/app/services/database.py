from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.connection import get_connection_string
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker


class DatabaseService:
    def __init__(self):
        connection_string : str = get_connection_string().replace("+asyncpg", "+psycopg2")
        self.engine : Engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_timeout=60,
            pool_pre_ping=True,  # Add connection health check
            pool_recycle=3600    # Recycle connections after 1 hour
        )
        self.session_factory : sessionmaker = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session directly"""
        return self.session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic commit/rollback"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()
    
    # TODO Use the get db with a context manager to terminate the session when finished in the api instead of using the get_session() method
    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI dependency for database sessions"""
        with self.session_scope() as session:
            yield session