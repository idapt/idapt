from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import HTTPException

class DatabaseService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic commit/rollback"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()
    
    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI dependency for database sessions"""
        with self.get_session() as session:
            yield session 