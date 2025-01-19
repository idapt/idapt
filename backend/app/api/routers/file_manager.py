from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
from base64 import urlsafe_b64decode

from app.api.models.models import FolderContentsResponse, FileResponse, FolderResponse
from app.api.models.file_models import FileUploadRequest, FileUploadItem
from app.database.models import File, Folder
from app.services.file_system import get_path_from_full_path, get_full_path_from_path, validate_path, get_existing_sanitized_path
from app.services.db_file import get_db_folder_contents, get_db_file
from app.services.file_manager import upload_file, upload_files, download_file, delete_file, delete_folder, rename_file, download_folder
from app.services.database import get_db_session
from app.api.dependencies import get_user_id

import logging

logger = logging.getLogger("uvicorn")

file_manager_router = r = APIRouter()

def decode_path_safe(encoded_original_path: str) -> str:
    try:
        return urlsafe_b64decode(encoded_original_path.encode()).decode()
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
        
        return await upload_file(item=item, session=session, user_id=user_id)
    except HTTPException as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@r.get("/file/{encoded_original_path}/download")
async def download_file_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        if not encoded_original_path:
            raise HTTPException(status_code=400, detail="Path parameter is required")
            
        original_path = decode_path_safe(encoded_original_path)
        logger.info(f"Downloading file {original_path} for user {user_id}")

        # Validate decoded path
        validate_path(original_path, session)

        # Convert it to the sanitized path used by the backend, if it exists it will return the existing path in the database corresponding to the original path
        full_path = get_existing_sanitized_path(session=session, original_path=original_path)
        logger.debug(f"Full path: {full_path}")
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


@r.delete("/{encoded_original_path}")
async def delete_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Deleting item {encoded_original_path} for user {user_id}")
        original_path = decode_path_safe(encoded_original_path)
        validate_path(original_path, session)
        
        # Convert it to the sanitized path used by the backend
        full_path = get_existing_sanitized_path(session=session, original_path=original_path)
        
        # Check if it's a file first
        file = session.query(File).filter(File.path == full_path).first()
        if file:
            await delete_file(session=session, user_id=user_id, full_path=full_path)
            return {"success": True}
            
        # If not a file, check if it's a folder
        folder = session.query(Folder).filter(Folder.path == full_path).first()
        if folder:
            await delete_folder(session=session, user_id=user_id, full_path=full_path)
            return {"success": True}
            
        # If neither found, return 404
        raise HTTPException(status_code=404, detail="Item not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete item")

#@r.put("/file/{encoded_original_path}/rename")
#async def rename_file_route(
#    encoded_original_path: str, 
#    new_name: str, 
#    user_id: str = Depends(get_user_id),
#    session: Session = Depends(get_db_session)
#):
#    logger.info(f"Renaming file {encoded_original_path} to {new_name} for user {user_id}")
#    path = decode_path_safe(encoded_original_path)
#    full_path = get_full_path_from_path(path, user_id)
#    await rename_file(session=session, user_id=user_id, full_path=full_path, new_name=new_name)
#    return {"success": True}

@r.get("/folder")
@r.get("/folder/")
@r.get("/folder/{encoded_original_path}")
async def get_folder_contents_route(
    encoded_original_path: str | None = None,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
) -> FolderContentsResponse:
    """Get contents of a folder"""
    try:
        logger.info(f"Getting folder contents for path: {encoded_original_path} for user {user_id}")
        if encoded_original_path:
            original_path = decode_path_safe(encoded_original_path)
            validate_path(original_path, session)
            logger.debug(f"Relative original path from home: {original_path}")
            # Convert it to the sanitized path used by the backend
            full_path = get_existing_sanitized_path(session=session, original_path=original_path)
        else:
            full_path = get_full_path_from_path("", user_id)
        logger.debug(f"Getting folder contents for path: {full_path}")
        files, folders = get_db_folder_contents(session=session, full_path=full_path)
        files = [FileResponse(
            id=file.id,
            name=file.name,
            # We are leaving the api so convert the full path to path
            path=get_path_from_full_path(file.path, user_id),
            original_path=get_path_from_full_path(file.original_path, user_id),
            mime_type=file.mime_type,
            size=file.size,
            uploaded_at=file.uploaded_at.timestamp(),
            accessed_at=file.accessed_at.timestamp(),
            file_created_at=file.file_created_at.timestamp(),
            file_modified_at=file.file_modified_at.timestamp(),
            stacks_to_process=file.stacks_to_process,
            processed_stacks=file.processed_stacks
        ) for file in files]
        folders = [FolderResponse(
            id=folder.id,
            name=folder.name,
            # We are leaving the api so convert the full path to path
            path=get_path_from_full_path(folder.path, user_id),
            original_path=get_path_from_full_path(folder.original_path, user_id),
            uploaded_at=folder.uploaded_at.timestamp(),
            accessed_at=folder.accessed_at.timestamp()
        ) for folder in folders]
        return FolderContentsResponse(files=files, folders=folders)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder contents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get folder contents")

@r.get("/folder/{encoded_original_path}/download")
async def download_folder_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Downloading folder {encoded_original_path} for user {user_id}")
        original_path = decode_path_safe(encoded_original_path)
        validate_path(original_path, session)
        # Convert it to the sanitized path used by the backend
        full_path = get_existing_sanitized_path(session=session, original_path=original_path)
        result = await download_folder(session, full_path)
        return Response(
            content=result["content"],
            media_type=result["mime_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading folder: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download folder")
