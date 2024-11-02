import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models import File, DataEmbeddings
from app.engine.node_processor import delete_nodes_for_file

logger = logging.getLogger(__name__)

def read_file_content(file_path: Path) -> Optional[str]:
    """Read content from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def create_file(session: Session, name: str, content: str, folder_id: Optional[int] = None) -> File:
    """Create or update a file in the database"""
    db_file = File(
        name=name,
        content=content,
        folder_id=folder_id
    )
    session.merge(db_file)
    session.flush()
    return db_file

def delete_file(session: Session, file_id: int):
    """Delete a file and its associated data"""
    delete_nodes_for_file(session, file_id)
    session.query(DataEmbeddings).filter_by(file_id=file_id).delete()
    session.query(File).filter_by(id=file_id).delete()