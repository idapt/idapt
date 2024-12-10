from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
from base64 import urlsafe_b64decode

from app.database.connection import get_db_session
from app.services.file_manager import FileManagerService
from app.api.routers.models import FileUploadRequest, FolderContentsResponse, FileResponse, FolderResponse

import logging
logger = logging.getLogger(__name__)

file_manager_router = r = APIRouter()
file_manager = FileManagerService()

def decode_path_safe(encoded_path: str) -> str:
    try:
        return urlsafe_b64decode(encoded_path.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path encoding")

@r.post("/upload")
async def upload_files(
    request: FileUploadRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session)
) -> EventSourceResponse:
    return EventSourceResponse(file_manager.upload_files(request, background_tasks, session))

@r.get("/file/{encoded_path}/download")
async def download_file(encoded_path: str, session: Session = Depends(get_db_session)):
    path = decode_path_safe(encoded_path)
    result = await file_manager.download_file(session, path)
    return Response(
        content=result["content"],
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}",
            "X-Creation-Time": str(result["created_at"]),
            "X-Modified-Time": str(result["modified_at"])
        }
    )

@r.delete("/file/{encoded_path}")
async def delete_file(encoded_path: str, session: Session = Depends(get_db_session)):
    path = decode_path_safe(encoded_path)
    await file_manager.delete_file(session, path)
    return {"success": True}

@r.delete("/folder/{encoded_path}")
async def delete_folder(encoded_path: str, session: Session = Depends(get_db_session)):
    path = decode_path_safe(encoded_path)
    await file_manager.delete_folder(session, path)
    return {"success": True}

@r.put("/file/{encoded_path}/rename")
async def rename_file(
    encoded_path: str, 
    new_name: str, 
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    await file_manager.rename_file(session, path, new_name)
    return {"success": True}

@r.get("/folder")
@r.get("/folder/")
async def get_root_folder(session: Session = Depends(get_db_session)) -> FolderContentsResponse:
    files, folders = file_manager.get_folder_contents(session, None)
    files = [FileResponse(**file.__dict__) for file in files]
    folders = [FolderResponse(**folder.__dict__) for folder in folders]
    return FolderContentsResponse(files=files, folders=folders)

@r.get("/folder/{encoded_path}")
async def get_folder_contents(
    encoded_path: str | None = None,
    session: Session = Depends(get_db_session)
) -> FolderContentsResponse:
    """Get contents of a folder"""
    path = None
    if encoded_path:
        path = decode_path_safe(encoded_path)
    files, folders = file_manager.get_folder_contents(session, path)
    files = [FileResponse(**file.__dict__) for file in files]
    folders = [FolderResponse(**folder.__dict__) for folder in folders]
    return FolderContentsResponse(files=files, folders=folders)

@r.get("/folder/{encoded_path}/download")
async def download_folder(encoded_path: str, session: Session = Depends(get_db_session)):
    path = decode_path_safe(encoded_path)
    result = await file_manager.download_folder(session, path)
    return Response(
        content=result["content"],
        media_type=result["mime_type"],
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}"
        }
    )
