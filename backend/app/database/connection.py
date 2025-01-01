import os
from pathlib import Path

def get_connection_string() -> str:
    """Get the database connection string for SQLite"""
    # Create the database directory if it doesn't exist
    db_dir = Path("/data/.idapt/db")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # SQLite database file path
    db_path = db_dir / "idapt.db"
    
    return f"sqlite:///{db_path}"