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