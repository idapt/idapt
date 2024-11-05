from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.services.file_manager import FileManagerService
from app.api.routers.models import FileNode
from app.services.db_file import DBFileService
from typing import List

file_manager_router = r = APIRouter()
file_manager = FileManagerService()

@r.get("/download/{file_id}")
async def download_file(file_id: int, session: Session = Depends(get_db_session)):
    result = await file_manager.download_file(session, file_id)
    return result

@r.delete("/file/{file_id}")
async def delete_file(file_id: int, session: Session = Depends(get_db_session)):
    await file_manager.delete_file(session, file_id)
    return {"success": True}

@r.delete("/folder/{folder_id}")
async def delete_folder(folder_id: int, session: Session = Depends(get_db_session)):
    await file_manager.delete_folder(session, folder_id)
    return {"success": True}

@r.put("/file/{file_id}/rename")
async def rename_file(
    file_id: int, 
    new_name: str, 
    session: Session = Depends(get_db_session)
):
    await file_manager.rename_file(session, file_id, new_name)
    return {"success": True}

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
