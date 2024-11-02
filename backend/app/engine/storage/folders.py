from typing import Dict, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from app.database.models import Folder

def create_folder(session: Session, name: str, parent_id: Optional[int] = None) -> Folder:
    """Create a new folder in the database"""
    folder = Folder(name=name, parent_id=parent_id)
    session.add(folder)
    session.flush()  # Flush to get the ID
    return folder

def get_or_create_folder(session: Session, folder_path: Path, folder_cache: Dict[str, Folder]) -> Folder:
    """Get or create a folder and its parent folders"""
    if str(folder_path) in folder_cache:
        return folder_cache[str(folder_path)]

    if str(folder_path.parent) == '.':
        folder = create_folder(session, folder_path.name)
    else:
        parent = get_or_create_folder(session, folder_path.parent, folder_cache)
        folder = create_folder(session, folder_path.name, parent.id)

    folder_cache[str(folder_path)] = folder
    return folder