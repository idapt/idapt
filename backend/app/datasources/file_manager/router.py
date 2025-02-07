from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import Response
#from fastapi.responses import FileResponse
from typing import Annotated

from app.datasources.file_manager.schemas import FileUploadItem, FileDownloadResponse, FolderDownloadResponse, FileInfoResponse, FolderInfoResponse, UpdateFileProcessingStatusRequest
from app.datasources.file_manager.service.service import upload_file, download_file, delete_item, download_folder, get_folder_info, get_file_info, update_file_processing_status
from app.auth.service import get_user_uuid_from_token
from app.datasources.file_manager.database.session import get_datasources_file_manager_db_session
from app.datasources.database.session import get_datasources_db_session
from app.datasources.file_manager.utils import decode_path_safe
from app.datasources.file_manager.service.llama_index import delete_item_from_llama_index
from app.datasources.file_manager.dependencies import validate_datasource_is_of_type_files
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
    datasource_name: str,
    item: FileUploadItem,
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
):
    try:
        logger.info(f"Uploading file {item.name} and datasource {datasource_name}")

        file_info = await upload_file(item=item, file_manager_session=file_manager_session, user_uuid=user_uuid)
    
        return file_info
    
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.delete("/{encoded_original_path}")
async def delete_route(
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
    original_path: Annotated[str, Depends(decode_path_safe)],
):
    try:
        logger.info(f"Deleting item {original_path}")

        await delete_item(file_manager_session=file_manager_session, user_uuid=user_uuid, original_path=original_path)

        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete item")
    
@r.get(
    "/folder/{encoded_original_path}",
    response_model=FolderInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get folder contents"
)
async def get_folder_info_route(
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
    original_path: Annotated[str, Depends(decode_path_safe)],
    include_child_folders_files_recursively: bool = False,
) -> FolderInfoResponse:
    """Get contents of a folder"""
    try:

        return get_folder_info(file_manager_session=file_manager_session, user_uuid=user_uuid, original_path=original_path, include_child_folders_files_recursively=include_child_folders_files_recursively)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder contents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get folder contents")

@r.get(
    "/file/{encoded_original_path}",
    response_model=FileInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get file info"
)
async def get_file_info_route(
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    original_path: Annotated[str, Depends(decode_path_safe)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
    include_content: bool = False,
):
    try:
        return await get_file_info(file_manager_session=file_manager_session, user_uuid=user_uuid, original_path=original_path, include_content=include_content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get file info")

@r.get(
    "/file/{encoded_original_path}/download",
    status_code=status.HTTP_200_OK,
    summary="Download file"
)
async def download_file_route(
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
    original_path: Annotated[str, Depends(decode_path_safe)],
):
    try:
        logger.info(f"Downloading file {original_path}")

        result: FileDownloadResponse = await download_file(file_manager_session=file_manager_session, user_uuid=user_uuid, original_path=original_path)
        
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
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
    original_path: Annotated[str, Depends(decode_path_safe)],
):
    try:
        logger.info(f"Downloading folder {original_path}")

        result: FolderDownloadResponse = await download_folder(file_manager_session=file_manager_session, user_uuid=user_uuid, original_path=original_path)
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

@r.delete("/processed-data/{encoded_original_path}")
async def delete_processed_data_route(
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    _: Annotated[str, Depends(validate_datasource_is_of_type_files)],
    file_manager_session: Annotated[Session, Depends(get_datasources_file_manager_db_session)],
    original_path: Annotated[str, Depends(decode_path_safe)],
):
    try:
        logger.info(f"Deleting processed data and path {original_path}")

        await delete_item_from_llama_index(file_manager_session=file_manager_session, user_uuid=user_uuid, original_path=original_path)

        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting processed data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete processed data")

# Unused for now
#@r.post("/file/process-callback")
#async def process_callback_route(
#    request: UpdateFileProcessingStatusRequest,
#    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
#    session: Annotated[Session, Depends(get_file_manager_db_session)],
#):
#    try:
#        logger.info(f"Processing callback for file {request.fs_path} with status {request.status}")
#
#        update_file_processing_status(
#            session=session,
#            fs_path=request.fs_path,
#            status=request.status,
#            stacks_to_process=request.stacks_to_process,
#            stack_being_processed=request.stack_being_processed,
#            processed_stack=request.processed_stack,
#            error_message=request.error_message,
#            erroring_stack=request.erroring_stack
#        )
#
#        return {"success": True}
#    except Exception as e:
#        logger.error(f"Error processing callback for file {request.fs_path}: {str(e)}")
#        raise HTTPException(status_code=500, detail="Failed to process callback")
