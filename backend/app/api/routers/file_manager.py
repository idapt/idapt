from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
from base64 import urlsafe_b64decode

from app.api.models.models import FolderContentsResponse, FileResponse, FolderResponse
from app.api.models.file_models import FileUploadRequest
from app.services.file_system import get_path_from_full_path, get_full_path_from_path
from app.services.file_manager import FileManagerService
from app.services import ServiceManager

import logging
logger = logging.getLogger(__name__)

file_manager_router = r = APIRouter()

def get_file_manager_service():
    return ServiceManager.get_instance().file_manager_service

def get_db_session():
    with ServiceManager.get_instance().db_service.get_session() as session:
        yield session

def decode_path_safe(encoded_path: str) -> str:
    try:
        return urlsafe_b64decode(encoded_path.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path encoding")

@r.post("/upload")
async def upload_files(
    request: FileUploadRequest,
    background_tasks: BackgroundTasks,
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
) -> EventSourceResponse:
    return EventSourceResponse(file_manager.upload_files(request, background_tasks, session))

@r.get("/file/{encoded_path}/download")
async def download_file(
    encoded_path: str,
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    result = await file_manager.download_file(session, full_path)
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
async def delete_file(
    encoded_path: str,
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    await file_manager.delete_file(session, full_path)
    return {"success": True}

@r.delete("/folder/{encoded_path}")
async def delete_folder(
    encoded_path: str,
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    await file_manager.delete_folder(session, full_path)
    return {"success": True}

@r.put("/file/{encoded_path}/rename")
async def rename_file(
    encoded_path: str, 
    new_name: str, 
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    await file_manager.rename_file(session, full_path, new_name)
    return {"success": True}

@r.get("/folder")
@r.get("/folder/")
@r.get("/folder/{encoded_path}")
async def get_folder_contents(
    encoded_path: str | None = None,
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
) -> FolderContentsResponse:
    """Get contents of a folder"""
    path = None
    if encoded_path:
        path = decode_path_safe(encoded_path)
    else:
        path = ""
    full_path = get_full_path_from_path(path)
    files, folders = file_manager.get_folder_contents(session, full_path)
    files = [FileResponse(
        id=file.id,
        name=file.name,
        # We are leaving the api so convert the full path to path
        path=get_path_from_full_path(file.path),
        mime_type=file.mime_type,
        size=file.size,
        uploaded_at=file.uploaded_at.timestamp(),
        accessed_at=file.accessed_at.timestamp(),
        file_created_at=file.file_created_at.timestamp(),
        file_modified_at=file.file_modified_at.timestamp()
    ) for file in files]
    folders = [FolderResponse(
        id=folder.id,
        name=folder.name,
        # We are leaving the api so convert the full path to path
        path=get_path_from_full_path(folder.path),
        uploaded_at=folder.uploaded_at.timestamp(),
        accessed_at=folder.accessed_at.timestamp()
    ) for folder in folders]
    return FolderContentsResponse(files=files, folders=folders)

@r.get("/folder/{encoded_path}/download")
async def download_folder(
    encoded_path: str,
    file_manager: FileManagerService = Depends(get_file_manager_service),
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    result = await file_manager.download_folder(session, full_path)
    return Response(
        content=result["content"],
        media_type=result["mime_type"],
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}"
        }
    )
