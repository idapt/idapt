from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
from base64 import urlsafe_b64decode

from app.api.models.models import FolderContentsResponse, FileResponse, FolderResponse
from app.api.models.file_models import FileUploadRequest, FileUploadItem
from app.services.file_system import get_path_from_full_path, get_full_path_from_path, validate_path
from app.services.db_file import get_db_folder_contents
from app.services.file_manager import upload_file, upload_files, download_file, delete_file, delete_folder, rename_file, download_folder
from app.services.database import get_db_session
from app.api.dependencies import get_user_id

import logging
logger = logging.getLogger("uvicorn")

file_manager_router = r = APIRouter()

def decode_path_safe(encoded_relative_path_from_home: str) -> str:
    try:
        return urlsafe_b64decode(encoded_relative_path_from_home.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path encoding")

@r.post("/upload-files")
async def upload_files_route(
    request: FileUploadRequest,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
) -> EventSourceResponse:
    try:
        logger.info(f"Uploading {len(request.items)} files for user {user_id}")
        for item in request.items:
            validate_path(item.relative_path_from_home, session)
        return EventSourceResponse(upload_files(request, session, user_id))
    except HTTPException as e:
        logger.error(f"Error during files upload: {str(e)}")
        raise e

@r.post("/upload-file")
async def upload_file_route(
    item: FileUploadItem,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Uploading file {item.name} for user {user_id}")
        logger.debug(f"File path: {item.relative_path_from_home}")
        
        validate_path(item.relative_path_from_home, session)
        return await upload_file(item=item, session=session, user_id=user_id)
    except HTTPException as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@r.get("/file/{encoded_relative_path_from_home}/download")
async def download_file_route(
    encoded_relative_path_from_home: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        if not encoded_relative_path_from_home:
            raise HTTPException(status_code=400, detail="Path parameter is required")
            
        logger.info(f"Downloading file {encoded_relative_path_from_home} for user {user_id}")
        relative_path_from_home = decode_path_safe(encoded_relative_path_from_home)
        
        # Validate decoded path
        validate_path(relative_path_from_home, session)
        
        full_path = get_full_path_from_path(relative_path_from_home, user_id)
        result = await download_file(session, full_path)
        
        if not result["content"]:
            raise HTTPException(status_code=404, detail="File content not found")
            
        return Response(
            content=result["content"],
            media_type=result["mime_type"] or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "Content-Length": str(len(result["content"])),
                "X-Creation-Time": str(result["created_at"]),
                "X-Modified-Time": str(result["modified_at"])
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download file")

@r.delete("/file/{encoded_relative_path_from_home}")
async def delete_file_route(
    encoded_relative_path_from_home: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    logger.info(f"Deleting file {encoded_relative_path_from_home} for user {user_id}")
    relative_path_from_home = decode_path_safe(encoded_relative_path_from_home)
    validate_path(relative_path_from_home, session)
    full_path = get_full_path_from_path(relative_path_from_home, user_id)
    await delete_file(session=session, user_id=user_id, full_path=full_path)
    return {"success": True}

@r.delete("/folder/{encoded_relative_path_from_home}")
async def delete_folder_route(
    encoded_relative_path_from_home: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    logger.info(f"Deleting folder {encoded_relative_path_from_home}")
    relative_path_from_home = decode_path_safe(encoded_relative_path_from_home)
    validate_path(relative_path_from_home)
    full_path = get_full_path_from_path(relative_path_from_home, user_id)
    await delete_folder(session=session, user_id=user_id, full_path=full_path)
    return {"success": True}

#@r.put("/file/{encoded_relative_path_from_home}/rename")
#async def rename_file_route(
#    encoded_relative_path_from_home: str, 
#    new_name: str, 
#    user_id: str = Depends(get_user_id),
#    session: Session = Depends(get_db_session)
#):
#    logger.info(f"Renaming file {encoded_relative_path_from_home} to {new_name} for user {user_id}")
#    path = decode_path_safe(encoded_relative_path_from_home)
#    full_path = get_full_path_from_path(path, user_id)
#    await rename_file(session=session, user_id=user_id, full_path=full_path, new_name=new_name)
#    return {"success": True}

@r.get("/folder")
@r.get("/folder/")
@r.get("/folder/{encoded_relative_path_from_home}")
async def get_folder_contents_route(
    encoded_relative_path_from_home: str | None = None,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
) -> FolderContentsResponse:
    """Get contents of a folder"""
    logger.info(f"Getting folder contents for path: {encoded_relative_path_from_home} for user {user_id}")
    relative_path_from_home = None
    if encoded_relative_path_from_home:
        relative_path_from_home = decode_path_safe(encoded_relative_path_from_home)
        validate_path(relative_path_from_home, session)
    else:
        relative_path_from_home = ""
    full_path = get_full_path_from_path(path=relative_path_from_home, user_id=user_id)
    files, folders = get_db_folder_contents(session=session, full_path=full_path)
    files = [FileResponse(
        id=file.id,
        name=file.name,
        # We are leaving the api so convert the full path to path
        path=get_path_from_full_path(file.path, user_id),
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
        path=get_path_from_full_path(folder.path, user_id),
        uploaded_at=folder.uploaded_at.timestamp(),
        accessed_at=folder.accessed_at.timestamp()
    ) for folder in folders]
    return FolderContentsResponse(files=files, folders=folders)

@r.get("/folder/{encoded_relative_path_from_home}/download")
async def download_folder_route(
    encoded_relative_path_from_home: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    logger.info(f"Downloading folder {encoded_relative_path_from_home} for user {user_id}")
    relative_path_from_home = decode_path_safe(encoded_relative_path_from_home)
    validate_path(relative_path_from_home, session)
    full_path = get_full_path_from_path(relative_path_from_home, user_id)
    result = await download_folder(session, full_path)
    return Response(
        content=result["content"],
        media_type=result["mime_type"],
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}"
        }
    )
