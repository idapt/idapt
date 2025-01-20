from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import Response

from app.file_manager.schemas import FileUploadItem, FolderContentsResponse, FileDownloadResponse, FolderDownloadResponse, FileInfoResponse
from app.database.models import File, Folder
from app.file_manager.service.file_system import get_existing_fs_path_from_db
from app.file_manager.service.service import upload_file, download_file, delete_item, download_folder, get_folder_content
from app.database.service import get_db_session
from app.api.utils import get_user_id
from app.file_manager.utils import decode_path_safe, validate_path

import logging

logger = logging.getLogger("uvicorn")

file_manager_router = r = APIRouter()

@r.post(
    "/upload-file",
    response_model=FileInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload file"
)
async def upload_file_route(
    item: FileUploadItem,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    try:
        logger.info(f"Uploading file {item.name} for user {user_id}")

        file_info = await upload_file(item=item, session=session, user_id=user_id)
    
        return file_info
    
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.delete("/{encoded_original_path}")
async def delete_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
    original_path: str = Depends(decode_path_safe),
):
    try:
        logger.info(f"Deleting item {original_path} for user {user_id}")

        await delete_item(session=session, user_id=user_id, original_path=original_path)
        
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete item")
    
@r.get(
    "/folder",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get root folder contents"
)
async def get_root_folder_contents_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    try:
        return get_folder_content(session=session, user_id=user_id, original_path="")
    except Exception as e:
        logger.error(f"Error getting root folder contents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get root folder contents")

@r.get(
    "/folder/{encoded_original_path}",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get folder contents"
)
async def get_folder_contents_route(
    encoded_original_path: str | None = None,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
    original_path: str = Depends(decode_path_safe)
) -> FolderContentsResponse:
    """Get contents of a folder"""
    try:

        return get_folder_content(session=session, user_id=user_id, original_path=original_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder contents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get folder contents")

@r.get(
    "/file/{encoded_original_path}/download",
    status_code=status.HTTP_200_OK,
    summary="Download file"
)
async def download_file_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
    original_path: str = Depends(decode_path_safe)
):
    try:
        logger.info(f"Downloading file {original_path} for user {user_id}")

        result: FileDownloadResponse = await download_file(session=session, original_path=original_path)
        
        # Use starlette response to return the file as it is a file download and not json
        return Response(
            content=result.content,
            media_type=result.media_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={result.filename}",
                "Content-Length": str(len(result.content)),
                "X-Creation-Time": str(result.created_at),
                "X-Modified-Time": str(result.modified_at)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download file")


@r.get("/folder/{encoded_original_path}/download")
async def download_folder_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
    original_path: str = Depends(decode_path_safe)
):
    try:
        logger.info(f"Downloading folder {encoded_original_path} for user {user_id}")

        result: FolderDownloadResponse = await download_folder(session=session, original_path=original_path)
        return Response(
            content=result.content,
            media_type=result.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={result.filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading folder: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download folder")
