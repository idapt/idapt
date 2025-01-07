from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
from base64 import urlsafe_b64decode

from app.api.models.models import FolderContentsResponse, FileResponse, FolderResponse
from app.api.models.file_models import FileUploadRequest
from app.services.file_system import get_path_from_full_path, get_full_path_from_path
from app.services.db_file import get_db_folder_contents
from app.services.file_manager import upload_files, download_file, delete_file, delete_folder, rename_file, download_folder
from app.services.database import get_db_session

import logging
logger = logging.getLogger(__name__)

file_manager_router = r = APIRouter()

def decode_path_safe(encoded_path: str) -> str:
    try:
        return urlsafe_b64decode(encoded_path.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path encoding")

@r.post("/upload")
async def upload_files_route(
    request: FileUploadRequest,
    session: Session = Depends(get_db_session)
) -> EventSourceResponse:
    return EventSourceResponse(upload_files(request, session))

@r.get("/file/{encoded_path}/download")
async def download_file_route(
    encoded_path: str,
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    result = await download_file(session, full_path)
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
async def delete_file_route(
    encoded_path: str,
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    await delete_file(session, full_path)
    return {"success": True}

@r.delete("/folder/{encoded_path}")
async def delete_folder_route(
    encoded_path: str,
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    await delete_folder(session, full_path)
    return {"success": True}

@r.put("/file/{encoded_path}/rename")
async def rename_file_route(
    encoded_path: str, 
    new_name: str, 
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    await rename_file(session, full_path, new_name)
    return {"success": True}

@r.get("/folder")
@r.get("/folder/")
@r.get("/folder/{encoded_path}")
async def get_folder_contents_route(
    encoded_path: str | None = None,
    session: Session = Depends(get_db_session)
) -> FolderContentsResponse:
    """Get contents of a folder"""
    logger.info(f"Getting folder contents for path: {encoded_path}")
    path = None
    if encoded_path:
        path = decode_path_safe(encoded_path)
    else:
        path = ""
    full_path = get_full_path_from_path(path)
    files, folders = get_db_folder_contents(session, full_path)
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
async def download_folder_route(
    encoded_path: str,
    session: Session = Depends(get_db_session)
):
    path = decode_path_safe(encoded_path)
    full_path = get_full_path_from_path(path)
    result = await download_folder(session, full_path)
    return Response(
        content=result["content"],
        media_type=result["mime_type"],
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}"
        }
    )
