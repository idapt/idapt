from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.services.db_file import DBFileService, get_db_session

file_manager_router = r = APIRouter()

class FileNode(BaseModel):
    id: int
    name: str
    type: str  # 'file' or 'folder'
    mime_type: str | None = None
    children: List['FileNode'] | None = None

@r.get("/folder")
async def get_root_folder_contents(
    session: Session = Depends(get_db_session)
) -> List[FileNode]:
    """Get contents of root folder"""
    return DBFileService.get_folder_contents(session, None)

@r.get("/folder/{folder_id}")
async def get_folder_contents(
    folder_id: int,
    session: Session = Depends(get_db_session)
) -> List[FileNode]:
    """Get contents of a specific folder"""
    return DBFileService.get_folder_contents(session, folder_id)