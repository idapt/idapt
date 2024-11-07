from fastapi import HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import os
import base64
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
import zipfile
import mimetypes
import re
from io import BytesIO
import asyncio
from fastapi import BackgroundTasks

from app.services.db_file import DBFileService
from app.services.file_system import FileSystemService
from app.database.models import File, Folder
from app.api.routers.models import FileUploadItem, FileUploadRequest, FileUploadProgress, FileNode
from app.services.llama_index import LlamaIndexService
from app.services.generate import GenerateService

import logging
logger = logging.getLogger(__name__)

class FileManagerService:
    def __init__(self):
        self.llama_index = LlamaIndexService()
        self.file_system = FileSystemService()

    async def upload_files(self, request: FileUploadRequest, background_tasks: BackgroundTasks, session: Session) -> AsyncGenerator[dict, None]:
        total = len(request.items)
        processed = []
        skipped = []
        file_paths = []
        
        print(f"Uploading {total} files")
        
        try:
            for idx, item in enumerate(request.items, 1):
                try:
                    print(f"Uploading file {idx}/{total}: {item.path}")
                    
                    result = await self.upload_file(session, item, file_paths)
                    if result:
                        processed.append(result)

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
                    print(f"Error uploading file: {str(e)}")
                    error_message = str(e)
                    yield {
                        "event": "message",
                        "data": FileUploadProgress(
                            total=total,
                            current=idx,
                            processed_items=processed + skipped,
                            status="error",
                            error=f"Error uploading {item.path}: {error_message}"
                        ).model_dump_json()
                    }
                    return

            # Trigger generate endpoint after successful upload only for files (not folders)
            if file_paths:
                background_tasks.add_task(
                    GenerateService.generate_embeddings,
                    file_paths
                )
            
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

    async def upload_file(self, session: Session, item: FileUploadItem, file_paths: list[str]) -> str:
        """Process a single upload item (file or folder)"""
        try:
            # Store full path for filesystem operations
            full_path = Path(convert_db_path_to_filesystem_path(item.path))
            
            # Get relative path for database operations
            db_path = item.path
            
            # Check if path already exists
            if DBFileService.path_exists(session, db_path):
                # Delete existing file/folder if it exists
                if item.is_folder:
                    folder = session.query(Folder).filter(Folder.path == db_path).first()
                    if folder:
                        DBFileService.delete_folder(session, folder.id)
                        await self.file_system.delete_folder(db_path)
                else:
                    file = session.query(File).filter(File.path == db_path).first()
                    if file:
                        result = await DBFileService.delete_file(session, file.id)
                        if not result:
                            logger.warning(f"Failed to delete file from database for id: {file.id}")
                        await self.file_system.delete_file(db_path)
            
            # Now proceed with the upload
            if item.is_folder:
                os.makedirs(str(full_path), exist_ok=True)
                DBFileService.create_folder_path(session, db_path)
            else:
                # Process and save file to disk
                os.makedirs(str(full_path.parent), exist_ok=True)
                file_data, _ = _preprocess_base64_file(item.content)
                await self.file_system.write_file(str(full_path), file_data)
                
                # Store file path for generation
                file_paths.append(db_path)
                
                # Create folder structure and file in database
                parent_path = str(Path(db_path).parent)
                folder = None if parent_path in ['', '.'] else DBFileService.create_folder_path(session, parent_path)
                
                DBFileService.create_file(
                    session=session,
                    name=item.name,
                    path=db_path,
                    folder_id=folder.id if folder else None,
                    original_created_at=item.original_created_at,
                    original_modified_at=item.original_modified_at
                )
                
                return f"Uploaded file: {item.path}"
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

    async def download_file(self, session: Session, file_id: int) -> Dict[str, str]:
        try:
            file = DBFileService.get_file(session, file_id)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Add idapt_data prefix to the path
            file_path = Path(os.getenv("STORAGE_PATH", "")) / "/idapt_data" / file.path

            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found on disk")

            # Get the file content from the filesystem
            with open(file_path, "rb") as f:
                file_content = f.read()

            return {
                "content": file_content,
                "filename": file.name,
                "created_at": file.original_created_at or file.created_at,
                "modified_at": file.original_modified_at or file.updated_at
            }
            
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            raise

    async def delete_file(self, session: Session, file_id: int):
        file = DBFileService.get_file(session, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Convert db file path to filesystem path
        filesystem_path = convert_db_path_to_filesystem_path(file.path)

        # Delete from filesystem with idapt_data prefix
        await self.file_system.delete_file(filesystem_path)
        
        # Delete from database
        result = await DBFileService.delete_file(session, file_id)
        if not result:
            logger.warning(f"Failed to delete file from database for id: {file_id}")

        # Remove from LlamaIndex
        result = await self.llama_index.remove_document(filesystem_path)
        if result is None:
            logger.warning(f"Failed to delete document from LlamaIndex for path: {filesystem_path}")

    async def delete_folder(self, session: Session, folder_id: int):
        folder = DBFileService.get_folder(session, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Get all files in folder and subfolders recursively
        files = DBFileService.get_folder_files_recursive(session, folder_id)
        
        # Delete all files in the folder and subfolders
        for file in files:
            # Use our delete_file method to delete from filesystem and LlamaIndex
            await self.delete_file(session, file.id)

        # Delete folder and all subfolders from filesystem
        await self.file_system.delete_folder(folder.path)

        # Delete folder from database (will cascade delete files and subfolders)
        DBFileService.delete_folder(session, folder_id)

    async def rename_file(self, session: Session, file_id: int, new_name: str):
        file = DBFileService.get_file(session, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Rename in filesystem
        new_path = await self.file_system.rename_file(file.path, new_name)
        
        # Update database
        updated_file = DBFileService.update_file(session, file_id, new_name, new_path)
        if not updated_file:
            raise HTTPException(status_code=500, detail="Failed to update file in database")

        # Update in LlamaIndex
        await self.llama_index.update_document(str(file_id), {
            "metadata": {"filename": new_name, "path": new_path}
        }) 

    async def download_folder(self, session: Session, folder_id: int) -> Dict[str, Any]:
        try:
            folder = DBFileService.get_folder(session, folder_id)
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            # Create a memory buffer for the zip file
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Get all files recursively
                files = DBFileService.get_folder_files_recursive(session, folder_id)
                
                for file in files:
                    # Calculate relative path within the zip
                    relative_path = file.path.replace(folder.path + '/', '')
                    
                    # Read file content
                    file_path = Path(os.getenv("STORAGE_PATH", "")) / "/idapt_data" / file.path
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            zip_file.writestr(relative_path, f.read())
            
            # Get the zip content
            zip_buffer.seek(0)
            zip_content = zip_buffer.getvalue()
            
            return {
                "content": zip_content,
                "filename": f"{folder.name}.zip",
                "mime_type": "application/zip"
            }
            
        except Exception as e:
            print(f"Error creating folder zip: {str(e)}")
            raise

def convert_filesystem_path_to_db_path(full_path: str | Path) -> str:
    """
    Normalize a full path by removing the DATA_DIR prefix and leading slashes.
    
    Args:
        full_path: The full path to normalize (can be string or Path object)
        
    Returns:
        str: Normalized path relative to DATA_DIR
    """
    from app.config import DATA_DIR
    return str(full_path).replace(str(DATA_DIR), '').lstrip('/')

def convert_db_path_to_filesystem_path(path: str) -> str:
    from app.config import DATA_DIR
    return str(Path(DATA_DIR) / path)

def _sanitize_file_name(file_name: str) -> str:
    """
    Sanitize the file name by replacing all non-alphanumeric characters with underscores
    """
    sanitized_name = re.sub(r"[^a-zA-Z0-9.]", "_", file_name)
    return sanitized_name

def _preprocess_base64_file(base64_content: str) -> Tuple[bytes, str | None]:
    header, data = base64_content.split(",", 1)
    mime_type = header.split(";")[0].split(":", 1)[1]
    extension = mimetypes.guess_extension(mime_type).lstrip(".")
    # File data as bytes
    return base64.b64decode(data), extension