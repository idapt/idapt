from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.connection import get_connection_string
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker


class DatabaseService:
    def __init__(self):
        connection_string = get_connection_string()
        self.engine: Engine = create_engine(
            connection_string,
            connect_args={"check_same_thread": False}  # Required for SQLite
        )
        self.session_factory = sessionmaker(bind=self.engine)
    
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