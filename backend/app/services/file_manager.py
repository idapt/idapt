from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, AsyncGenerator, Tuple
import zipfile
from io import BytesIO
import asyncio
import base64
import os
import time

# The services are already initialized in the main.py file
from app.services.db_file import get_db_file, delete_db_file, update_db_file, get_db_folder_files_recursive, get_db_folder, delete_db_folder
from app.services.file_system import get_existing_sanitized_path, validate_path, write_file_filesystem, read_file_filesystem, delete_file_filesystem, rename_file_filesystem, delete_folder_filesystem, get_new_sanitized_path
from app.services.llama_index import delete_file_llama_index
from app.api.models.file_models import FileUploadItem, FileUploadRequest, FileUploadProgress
from app.database.models import FileStatus, File, Folder

import logging

logger = logging.getLogger("uvicorn")

async def upload_files(request: FileUploadRequest, session: Session, user_id: str) -> AsyncGenerator[dict, None]:
    try:
        total = len(request.items)
        processed = []
        skipped = []
        
        logger.info(f"Uploading {total} files")
        
        for idx, item in enumerate(request.items, 1):
            try:
                logger.info(f"Uploading file {idx}/{total}: {item.relative_path_from_home}")
                
                result = await upload_file(session, item, user_id)
                if result:
                    processed.append(result["path"])

                yield {
                    "event": "message",
                    "data": FileUploadProgress(
                        total=total,
                        current=idx,
                        processed_items=processed + skipped,
                        status="processing"
                    ).model_dump_json()
                }
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error uploading file {item.relative_path_from_home}: {str(e)}")
                error_message = str(e)
                yield {
                    "event": "message",
                    "data": FileUploadProgress(
                        total=total,
                        current=idx,
                        processed_items=processed + skipped,
                        status="error",
                        error=f"Error uploading {item.relative_path_from_home}: {error_message}"
                    ).model_dump_json()
                }
                return

        
        # Final success message
        yield {
            "event": "message",
            "data": FileUploadProgress(
                total=total,
                current=total,
                processed_items=processed + skipped,
                status="completed"
            ).model_dump_json()
        }

    except Exception as e:
        logger.error(f"Error during file upload process: {str(e)}")
        yield {
            "event": "message",
            "data": FileUploadProgress(
                total=total,
                current=0,
                processed_items=[],
                status="error",
                error=f"Upload failed: {str(e)}"
            ).model_dump_json()
        }

async def upload_file(session: Session, item: FileUploadItem, user_id: str) -> Dict[str, Any]:
    try:
        # Validate path
        validate_path(item.relative_path_from_home, session)

        # Validate basic input parameters
        if not item:
            raise HTTPException(status_code=400, detail="Upload item cannot be empty")
            
        # Validate file content
        if not item.base64_content:
            raise HTTPException(status_code=400, detail="File content cannot be empty")
            
        try:
            # Validate base64 format
            if not item.base64_content.startswith('data:'):
                raise HTTPException(status_code=400, detail="Invalid base64 content format")
                
            # Extract content type and base64 data
            content_parts = item.base64_content.split(',', 1)
            if len(content_parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid base64 content format")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {str(e)}")
            
        # Validate file metadata
        if item.file_created_at and item.file_created_at < 0:
            raise HTTPException(status_code=400, detail="Invalid file creation timestamp")
            
        if item.file_modified_at and item.file_modified_at < 0:
            raise HTTPException(status_code=400, detail="Invalid file modification timestamp")
        
        full_path = None
        # Get sanitized paths
        try:
            #This will create or get the folders if they already exist by original path and if not it will create them minding existing ones
            full_path = get_new_sanitized_path(
                item.relative_path_from_home, 
                user_id, 
                session
            )
            logger.debug(f"Full path: {full_path}")
        # If the path already exists and an http error 400 error is raised, get the full path with get_existing_sanitized_path instead
        except HTTPException as e:
            if e.status_code == 400 and e.detail == f"File already exists":
                # TODO Implement conflict resolution, for now overwrite
                full_path = get_existing_sanitized_path(session=session, original_path=item.relative_path_from_home)
            else:
                raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error during file upload: {str(e)}")
        
        # Check if original path exists (handle overwrite)
        existing_file = session.query(File).filter(
            File.original_path == item.relative_path_from_home
        ).first()
        
        if existing_file:
            # Check if file is being processed before allowing overwrite
            if existing_file.status == FileStatus.PROCESSING:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot overwrite file that is currently being processed"
                )
            # Delete existing file
            await delete_file(session, user_id, existing_file.path)
            
        # Process file content and write to filesystem
        try:

            decoded_file_data, mime_type = preprocess_base64_file(item.base64_content)
            
            # Validate file size (example: 100MB limit)
            #if len(decoded_file_data) > 100 * 1024 * 1024:
            #    raise HTTPException(
            #        status_code=400,
            #        detail="File size exceeds maximum limit of 100MB"
            #    )
            
                
            await write_file_filesystem(
                full_path=full_path,
                content=decoded_file_data,
                created_at_unix_timestamp=item.file_created_at or time.time(),
                modified_at_unix_timestamp=item.file_modified_at or time.time()
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error writing file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to write file to filesystem")

        # Create database entry with error handling
        try:
            # Get parent folder id
            parent_folder_path = str(Path(full_path).parent)
            parent_folder = session.query(Folder).filter(Folder.path == parent_folder_path).first()
            if not parent_folder:
                raise ValueError(f"Parent folder {parent_folder_path} not found")
            
            # Create file
            file = File(
                name=item.name,
                path=full_path,
                original_path=item.relative_path_from_home,
                size=len(decoded_file_data),
                mime_type=mime_type,
                folder_id=parent_folder.id,
                file_created_at=datetime.fromtimestamp(item.file_created_at) if item.file_created_at else datetime.now(),
                file_modified_at=datetime.fromtimestamp(item.file_modified_at) if item.file_modified_at else datetime.now()
            )
            session.add(file)
            session.commit()
        except Exception as e:
            # Clean up filesystem file if database insert fails
            await delete_file_filesystem(full_path)
            session.rollback()
            logger.error(f"Error creating database entry: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to create database entry for file"
            )

        return {
            "path": item.relative_path_from_home,
            "relative_path": full_path,
            "id": file.id,
            "mime_type": mime_type,
            "size": len(decoded_file_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during file upload"
        )

async def download_file(session: Session, full_path: str) -> Dict[str, str]:
    try:
        # First try to get file from database to see fast if it exists
        file = get_db_file(session, full_path)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file content from filesystem
        file_content = await read_file_filesystem(full_path)

        return {
            "content": file_content,
            "filename": file.name,
            "mime_type": file.mime_type,
            "size": file.size,
            "created_at": file.file_created_at,
            "modified_at": file.file_modified_at
        }
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise

async def delete_file(session: Session, user_id: str, full_path: str):
    try:
        logger.info(f"Deleting file {full_path} for user {user_id}")
        file = get_db_file(session, full_path)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if file is being processed
        if file.status in [FileStatus.PROCESSING]:
            raise HTTPException(
                status_code=409,
                detail="File is currently being processed and cannot be deleted"
            )

        # Proceed with deletion
        await delete_file_filesystem(full_path)
        delete_file_llama_index(session=session, user_id=user_id, full_path=full_path)
        result = delete_db_file(session=session, full_path=full_path)
        
        if not result:
            logger.warning(f"Failed to delete file from database for path: {full_path}")
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise

async def delete_folder(session: Session, user_id: str, full_path: str):
    # TODO Make more robust to avoid partial deletion
    try:
        logger.info(f"Deleting folder: {full_path}")

        folder = get_db_folder(session, full_path)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Get all files in folder and subfolders recursively
        files, subfolders = get_db_folder_files_recursive(session, full_path)
        
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

                await delete_file(session=session, user_id=user_id, full_path=file.path)
                delete_file_llama_index(session=session, user_id=user_id, full_path=file.path)
                delete_db_file(session=session, full_path=file.path)
                deleted_files.append(file.path)
            except Exception as e:
                logger.warning(f"Error deleting file {file.path}: {str(e)}")
                failed_files.append(file.path)
                continue

        # Delete folder from filesystem if no files are being processed
        if not processing_files:
            await delete_folder_filesystem(full_path)
            
            # Delete everything from database in one transaction
            if not delete_db_folder(session, full_path):
                raise HTTPException(status_code=500, detail="Failed to delete folder from database")
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
async def rename_file(session: Session, user_id: str, full_path: str, new_name: str):
    try:
        file = get_db_file(session, full_path)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Rename in filesystem
        await rename_file_filesystem(full_path, new_name)
        
        new_full_path = file.path.replace(file.name, new_name)
        
        # Update database
        updated_file = update_db_file(session=session, full_path=full_path, new_full_path=new_full_path)
        if not updated_file:
            raise HTTPException(status_code=500, detail="Failed to update file in database")

        # Update in LlamaIndex
        #rename_file_llama_index(session=session, user_id=user_id, full_old_path=full_path, full_new_path=new_full_path) 

    except Exception as e:
        logger.error(f"Error renaming file: {str(e)}")
        raise

async def download_folder(session: Session, full_path: str) -> Dict[str, Any]:
    try:

        # Get folder from database
        folder = get_db_folder(session, full_path)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Create a memory buffer for the zip file
        zip_buffer = BytesIO()
        
        # Create zip file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Get all files recursively
            files, _ = get_db_folder_files_recursive(session, full_path)
            
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
        
        return {
            "content": zip_content,
            "filename": f"{folder.name}.zip",
            "mime_type": "application/zip"
        }
        
    except Exception as e:
        logger.error(f"Error creating folder zip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating folder zip: {str(e)}")

                
def preprocess_base64_file(base64_content: str) -> Tuple[bytes, str | None]:
    """ Decode base64 file content and return the file data and extension """
    try:
        # Validate base64 content format
        if ',' not in base64_content:
            raise ValueError(
                "Invalid base64 format. Expected format: 'data:<mediatype>;base64,<data>'"
            )
            
        header, data = base64_content.split(",", 1)
        
        # Validate header format
        if not header.startswith('data:') or ';base64' not in header:
            raise ValueError(
                "Invalid base64 header format. Expected format: 'data:<mediatype>;base64'"
            )
            
        try:
            mime_type = header.split(";")[0].split(":", 1)[1]
        except IndexError:
            raise ValueError("Could not extract mime type from base64 header")

        # Decode base64 data
        try:
            decoded_data = base64.b64decode(data)
        except Exception:
            raise ValueError("Invalid base64 data encoding")

        return decoded_data, mime_type

    except ValueError as e:
        logger.error(f"Error preprocessing base64 file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error preprocessing base64 file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing file upload"
        )