from datetime import datetime
import json
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
import zipfile
from io import BytesIO
import os
import time
from typing import List

# The services are already initialized in the main.py file
from app.datasources.file_manager.service.db_operations import get_db_folder_files_recursive, delete_db_folder_recursive
from app.datasources.file_manager.service.file_system import get_path_from_fs_path, get_existing_fs_path_from_db, write_file_filesystem, read_file_filesystem, delete_file_filesystem, rename_file_filesystem, delete_folder_filesystem, get_new_fs_path
from app.datasources.file_manager.service.llama_index import delete_file_llama_index
from app.datasources.file_manager.schemas import FileUploadItem, FileDownloadResponse, FileInfoResponse, FolderInfoResponse, FolderDownloadResponse
from app.datasources.file_manager.database.models import FileStatus, File, Folder
from app.datasources.file_manager.utils import validate_path, preprocess_base64_file 
from app.api.user_path import get_user_data_dir

import logging

logger = logging.getLogger("uvicorn")

def initialize_file_manager_db(file_manager_session: Session, user_id: str, datasource_name: str):
    # Create the parent directories if they don't exist
    #db_path = Path(get_user_data_dir(user_id), datasource_name, "file_manager.db")    
    # Create the files directory for this datasource
    #files_dir = Path(get_user_data_dir(user_id), datasource_name, "files")
    #files_dir.mkdir(parents=True, exist_ok=True)

    # If the root folder for this datasource do not exist in the file manager db, create it
    root_folder = file_manager_session.query(Folder).filter(Folder.original_path == datasource_name).first()
    if not root_folder:
        fs_path = Path(get_user_data_dir(user_id)) / datasource_name
        #get_new_fs_path(datasource_name, file_manager_session, last_path_part_is_file=False)
        folder = Folder(
            name=datasource_name,
            path=str(fs_path),
            original_path=datasource_name,
            parent_id=None
        )
        file_manager_session.add(folder)
        file_manager_session.commit()
        logger.info(f"Initialized file manager db for datasource {datasource_name} with root folder {folder.path}")

async def upload_file(file_manager_session: Session, item: FileUploadItem, user_id: str) -> FileInfoResponse:
    try:

        # Validate path and raise if invalid
        validate_path(item.original_path)

        # Validate file content
        if not item.base64_content:
            raise HTTPException(status_code=400, detail="File content cannot be empty")
            
        # Validate base64 format
        if not item.base64_content.startswith('data:'):
            raise HTTPException(status_code=400, detail="Invalid base64 content format")
            
        # Extract content type and base64 data
        content_parts = item.base64_content.split(',', 1)
        if len(content_parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid base64 content format")

        # Validate file metadata
        if item.file_created_at and item.file_created_at < 0:
            raise HTTPException(status_code=400, detail="Invalid file creation timestamp")
            
        if item.file_modified_at and item.file_modified_at < 0:
            raise HTTPException(status_code=400, detail="Invalid file modification timestamp")
        
        fs_path = None
        # Get fs paths
        try:
            #This will create or get the folders if they already exist by original path and if not it will create them minding existing ones
            fs_path = get_new_fs_path(
                item.original_path, 
                file_manager_session,
                last_path_part_is_file=True
            )
        # If the path already exists and an http error 400 error is raised, get the full path with get_existing_fs_path instead
        except HTTPException as e:
            if e.status_code == 400 and "File already exists" in e.detail:
                # TODO Implement conflict resolution, for now overwrite
                fs_path = get_existing_fs_path_from_db(file_manager_session=file_manager_session, original_path=item.original_path)
            else:
                raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error during file upload: {str(e)}")
        
        # Check if original path exists (handle overwrite)
        existing_file = file_manager_session.query(File).filter(
            File.original_path == item.original_path
        ).first()
        
        if existing_file:
            # Check if file is being processed before allowing overwrite
            if existing_file.status == FileStatus.PROCESSING:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot overwrite file that is currently being processed"
                )
            # Delete existing file
            await delete_file(file_manager_session, user_id, existing_file.path)
            
        # Process file content and write to filesystem
        decoded_file_data, mime_type = preprocess_base64_file(item.base64_content)       
            
        await write_file_filesystem(
            fs_path=fs_path,
            content=decoded_file_data,
            created_at_unix_timestamp=item.file_created_at or time.time(),
            modified_at_unix_timestamp=item.file_modified_at or time.time()
        )

        # Create database entry with error handling
        try:
            # Get parent folder id
            parent_folder_path = str(Path(fs_path).parent)
            parent_folder = file_manager_session.query(Folder).filter(Folder.path == parent_folder_path).first()
            if not parent_folder:
                raise ValueError(f"Parent folder {parent_folder_path} not found")
            
            # Create file
            file = File(
                name=item.name,
                path=fs_path,
                original_path=item.original_path,
                size=len(decoded_file_data),
                mime_type=mime_type,
                folder_id=parent_folder.id,
                file_created_at=datetime.fromtimestamp(item.file_created_at) if item.file_created_at else datetime.now(),
                file_modified_at=datetime.fromtimestamp(item.file_modified_at) if item.file_modified_at else datetime.now()
            )
            file_manager_session.add(file)
            file_manager_session.commit()
        except Exception as e:
            # Clean up filesystem file if database insert fails
            await delete_file_filesystem(fs_path)
            file_manager_session.rollback()
            logger.error(f"Error creating database entry: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to create database entry for file"
            )

        # Get file content
        file_content = await read_file_filesystem(fs_path)

        return FileInfoResponse(
            id=file.id,
            name=file.name,
            path=get_path_from_fs_path(file.path, user_id),
            original_path=file.original_path,
            content=None, # Not included here as not useful
            mime_type=file.mime_type,
            size=file.size,
            uploaded_at=file.uploaded_at.timestamp(),
            accessed_at=file.accessed_at.timestamp(),
            file_created_at=file.file_created_at.timestamp(),
            file_modified_at=file.file_modified_at.timestamp(),
            stacks_to_process=file.stacks_to_process,
            processed_stacks=file.processed_stacks,
            error_message=file.error_message,
            status=file.status
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during file upload"
        )
    
async def get_file_info(file_manager_session: Session, user_id: str, original_path: str, include_content: bool = False) -> FileInfoResponse:
    try:
        # Validate path
        validate_path(original_path)

        # Get file from database
        file = file_manager_session.query(File).filter(File.original_path == original_path).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        if include_content:
            file_content = await read_file_filesystem(file.path)
        else:
            file_content = None

        return FileInfoResponse(
            id=file.id,
            name=file.name,
            # We are leaving the api so convert the full path to path
            path=get_path_from_fs_path(file.path, user_id),
            original_path=file.original_path,
            content=file_content,
            mime_type=file.mime_type,
            size=file.size,
            uploaded_at=file.uploaded_at.timestamp(),
            accessed_at=file.accessed_at.timestamp(),
            file_created_at=file.file_created_at.timestamp(),
            file_modified_at=file.file_modified_at.timestamp(),
            stacks_to_process=file.stacks_to_process,
            processed_stacks=file.processed_stacks,
            error_message=file.error_message,
            status=file.status
        )
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get file info")
    
def get_folder_info(file_manager_session: Session, user_id: str, original_path: str, include_child_folders_files_recursively: bool = False) -> FolderInfoResponse:
    try:
        logger.info(f"Getting folder contents for path: {original_path} for user {user_id}")
        
        # Validate path
        validate_path(original_path)

        # Convert it to the fs path used by the backend
        fs_path = get_existing_fs_path_from_db(file_manager_session=file_manager_session, original_path=original_path)

        # Get folder from path
        folder = file_manager_session.query(Folder).filter(Folder.path == fs_path).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Get all folders in this folder
        child_folders_db = file_manager_session.query(Folder).filter(Folder.parent_id == folder.id).all()
        # Get the child folders recursively or not depending on the parameter
        child_folders = [FolderInfoResponse(
            id=child_folder_db.id,
            name=child_folder_db.name,
            path=get_path_from_fs_path(child_folder_db.path, user_id),
            original_path=child_folder_db.original_path,
            uploaded_at=child_folder_db.uploaded_at.timestamp(),
            accessed_at=child_folder_db.accessed_at.timestamp(),
            child_files=[],
            child_folders=[]
        ) for child_folder_db in child_folders_db]
        if include_child_folders_files_recursively:
            for child_folder_db in child_folders_db:
                child_folders.append(get_folder_info(file_manager_session=file_manager_session, user_id=user_id, original_path=child_folder_db.original_path, include_child_folders_files_recursively=include_child_folders_files_recursively))
        
        # Get files in this folder
        child_files_db = file_manager_session.query(File).filter(File.folder_id == folder.id).all()
        child_files = [FileInfoResponse(
                id=file.id,
                name=file.name,
                # We are leaving the api so convert the full path to path
                path=get_path_from_fs_path(file.path, user_id),
                original_path=file.original_path,
                mime_type=file.mime_type,
                size=file.size,
                uploaded_at=file.uploaded_at.timestamp(),
                accessed_at=file.accessed_at.timestamp(),
                file_created_at=file.file_created_at.timestamp(),
                file_modified_at=file.file_modified_at.timestamp(),
                stacks_to_process=file.stacks_to_process,
                processed_stacks=file.processed_stacks,
                error_message=file.error_message,
                status=file.status
            ) for file in child_files_db]

        return FolderInfoResponse(
            id=folder.id,
            name=folder.name,
            # We are leaving the api so convert the full path to path
            path=get_path_from_fs_path(folder.path, user_id),
            original_path=folder.original_path,
            uploaded_at=folder.uploaded_at.timestamp(),
            accessed_at=folder.accessed_at.timestamp(),
            child_files=child_files,
            child_folders=child_folders
        )
    
    except Exception as e:
        logger.error(f"Error getting folder content: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting folder content")

async def download_file(file_manager_session: Session, user_id: str, original_path: str) -> FileDownloadResponse:
    try:
        # Validate path and raise if invalid
        validate_path(original_path)
        
        # Get file from database
        file = file_manager_session.query(File).filter(File.original_path == original_path).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Read file content
        content = await read_file_filesystem(file.path)
        
        # Get file stats
        file_stats = os.stat(file.path)
        
        return FileDownloadResponse(
            content=content,
            filename=file.name,
            media_type=file.mime_type or "application/octet-stream",
            created_at=file_stats.st_ctime,  # Unix timestamp
            modified_at=file_stats.st_mtime  # Unix timestamp
        )

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise

async def delete_item(file_manager_session: Session, user_id: str, original_path: str):
    """ 
    Delete the item at the given original path 
    If it's a file, delete it
    If it's a folder, delete it and child files and folders recursively
    """
    try:
        # Validate path and raise if invalid
        validate_path(original_path)

        # Convert it to the fs path used by the backend
        fs_path = get_existing_fs_path_from_db(file_manager_session=file_manager_session, original_path=original_path)
        
        # Check if it's a file first
        file = file_manager_session.query(File).filter(File.path == fs_path).first()
        if file:
            await delete_file(file_manager_session=file_manager_session, user_id=user_id, fs_path=fs_path)
            return {"success": True}
            
        # If not a file, check if it's a folder
        folder = file_manager_session.query(Folder).filter(Folder.path == fs_path).first()
        if folder:
            await delete_folder(file_manager_session=file_manager_session, user_id=user_id, fs_path=fs_path)
            return {"success": True}
            
        # If neither found, return 404
        raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        logger.error(f"Error deleting file from database: {str(e)}")
        raise e

async def delete_file(file_manager_session: Session, user_id: str, fs_path: str):
    try:
        logger.info(f"Deleting file {fs_path} for user {user_id}")

        
        file = file_manager_session.query(File).filter(File.path == fs_path).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if file is being processed
        if file.status in [FileStatus.PROCESSING]:
            raise HTTPException(
                status_code=409,
                detail="File is currently being processed and cannot be deleted"
            )

        # Proceed with deletion
        await delete_file_filesystem(fs_path)
        delete_file_llama_index(file_manager_session=file_manager_session, user_id=user_id, file=file)
        # Delete from database
        file_manager_session.delete(file)
        file_manager_session.commit()
        
    except Exception as e:
        file_manager_session.rollback()
        logger.error(f"Error deleting file: {str(e)}")
        raise

async def delete_folder(file_manager_session: Session, user_id: str, fs_path: str):
    # TODO Make more robust to avoid partial deletion by implementing a trash folder and moving the files to it and restoring them in case of an error
    try:
        logger.info(f"Deleting folder: {fs_path} for user {user_id}")


        folder = file_manager_session.query(Folder).filter(Folder.path == fs_path).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Get all files in folder and subfolders recursively
        files, subfolders = get_db_folder_files_recursive(file_manager_session, fs_path)
        
        processing_files = []
        deleted_files = []
        failed_files = []

        # First delete from filesystem and LlamaIndex
        for file in files:
            try:
                # Skip files that are being processed
                if file.status in [FileStatus.PROCESSING]:
                    processing_files.append(file.path)
                    continue

                await delete_file(file_manager_session=file_manager_session, user_id=user_id, fs_path=file.path)
                delete_file_llama_index(file_manager_session=file_manager_session, user_id=user_id, file=file)
                file_manager_session.delete(file)
                file_manager_session.commit()
                deleted_files.append(file.path)
            except Exception as e:
                logger.warning(f"Error deleting file {file.path}: {str(e)}")
                failed_files.append(file.path)
                continue

        # Delete folder from filesystem if no files are being processed
        if not processing_files:
            await delete_folder_filesystem(fs_path)
            
            # Delete everything from database in one transaction
            delete_db_folder_recursive(file_manager_session, fs_path)

        else:
            # Raise an exception with information about processing files
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Some files are being processed and cannot be deleted",
                    "processing_files": processing_files,
                    "deleted_files": deleted_files,
                    "failed_files": failed_files
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Unused
async def rename_file(file_manager_session: Session, user_id: str, fs_path: str, new_name: str):
    try:

        file = file_manager_session.query(File).filter(File.path == fs_path).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Rename in filesystem
        await rename_file_filesystem(fs_path, new_name)
        
        new_fs_path = file.path.replace(file.name, new_name)
        
        # Update database
        #updated_file =
        #if not updated_file:
        #    raise HTTPException(status_code=500, detail="Failed to update file in database")

        # Update in LlamaIndex
        #rename_file_llama_index(session=session, user_id=user_id, full_old_path=fs_path, full_new_path=new_fs_path) 

    except Exception as e:
        logger.error(f"Error renaming file: {str(e)}")
        raise

async def download_folder(file_manager_session: Session, user_id: str, original_path: str) -> FolderDownloadResponse:
    try:
        # Validate path and raise if invalid
        validate_path(original_path)

        # Convert it to the fs path used by the backend
        fs_path = get_existing_fs_path_from_db(file_manager_session=file_manager_session, original_path=original_path)
        # Get folder from database
        folder = file_manager_session.query(Folder).filter(Folder.path == fs_path).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Create a memory buffer for the zip file
        zip_buffer = BytesIO()
        
        # Create zip file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Get all files recursively
            files, _ = get_db_folder_files_recursive(file_manager_session, fs_path)
            
            # Iterate over all retrieved files
            for file in files:
                # TODO Make it work with original paths
                # Calculate relative path within the zip
                relative_path = os.path.relpath(file.path, folder.path)
                
                # Read file content
                file_content = await read_file_filesystem(file.path)

                # Write file content to zip
                if file_content:
                    zip_file.writestr(relative_path, file_content)
        
        # Get the zip content
        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        
        return FolderDownloadResponse(
            content=zip_content,
            filename=f"{folder.name}.zip",
            mime_type="application/zip"
        )
        
    except Exception as e:
        logger.error(f"Error creating folder zip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating folder zip: {str(e)}")

def update_file_processing_status(
        file_manager_session: Session,
        fs_path: str,
        status: str,
        stacks_to_process: List[str] | None = None,
        stack_being_processed: str | None = None,
        processed_stack: str | None = None,
        erroring_stack: str | None = None,
        error_message: str | None = None
    ):
    """
    Update the file processing status and related fields in the database based on the parameters given
    """
    try:

        # Get the file from the database
        file = file_manager_session.query(File).filter(File.path == fs_path).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # If we set status to queued
        if status == "QUEUED":
            # Add the stacks to process to the existing stacks to process json string
            file_stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
            for stack_identifier in stacks_to_process:
                if stack_identifier not in file_stacks_to_process:
                    file_stacks_to_process.append(stack_identifier)
            file.stacks_to_process = json.dumps(file_stacks_to_process)
            file.status = FileStatus.QUEUED
            file_manager_session.commit()
            return
        elif status == "PROCESSING":
            file.error_message = None
            file.status = FileStatus.PROCESSING
            file_manager_session.commit()
            return
        elif status == "COMPLETED":
            # Remove the processed stack from stacks to process
            file_stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
            if processed_stack and processed_stack in file_stacks_to_process:
                file_stacks_to_process.remove(processed_stack)
            file.stacks_to_process = json.dumps(file_stacks_to_process)
            # Add the processed stack to processed stacks of the file
            file_processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
            if processed_stack and processed_stack not in file_processed_stacks:
                file_processed_stacks.append(processed_stack)
            file.processed_stacks = json.dumps(file_processed_stacks)
            file.status = FileStatus.COMPLETED
            file_manager_session.commit()
            return
        elif status == "ERROR":
            # Remove the erroring stack from stacks to process
            file_stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
            if erroring_stack and erroring_stack in file_stacks_to_process:
                file_stacks_to_process.remove(erroring_stack)
            file.stacks_to_process = json.dumps(file_stacks_to_process)
            file.error_message = error_message
            file.status = FileStatus.ERROR
            file_manager_session.commit()
            return
        
        raise HTTPException(status_code=400, detail="Invalid status")

    except Exception as e:
        logger.error(f"Error updating file processing status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update file processing status")