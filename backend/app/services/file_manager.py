from fastapi import HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, List, Tuple
import zipfile
from io import BytesIO
import asyncio
from fastapi import BackgroundTasks
import base64
import mimetypes
import os

from app.services.db_file import DBFileService
from app.services.file_system import FileSystemService
from app.api.routers.models import FileUploadItem, FileUploadRequest, FileUploadProgress
from app.database.models import File, Folder
from app.services.llama_index import LlamaIndexService

import logging

class FileManagerService:
    """
    Service for managing files and folders
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_file_service = DBFileService()
        self.file_system = FileSystemService()
        self.llama_index = LlamaIndexService()

    async def upload_files(self, request: FileUploadRequest, background_tasks: BackgroundTasks, session: Session) -> AsyncGenerator[dict, None]:
        try:
            total = len(request.items)
            processed = []
            skipped = []
            
            self.logger.info(f"Uploading {total} files")
            
            for idx, item in enumerate(request.items, 1):
                try:
                    self.logger.info(f"Uploading file {idx}/{total}: {item.path}")
                    
                    result = await self.upload_file(session, item)
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
                    self.logger.error(f"Error uploading file {item.path}: {str(e)}")
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
            self.logger.error(f"Error during file upload process: {str(e)}")
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

    async def upload_file(self, session: Session, item: FileUploadItem) -> str:
        """Process a single upload item (file or folder)"""
        try:
            # Log the start of the upload process
            self.logger.info(f"Starting upload for file: {item.name}")
        

            # Decode the base64 file content into text
            decoded_file_data, _ = self.preprocess_base64_file(item.content)
            # Write file to filesystem
            await self.file_system.write_file(item.path, decoded_file_data)


            # Create file in database
            file = self.db_file_service.create_file(
                session=session,
                name=item.name,
                path=item.path,
                original_created_at=item.original_created_at,
                original_modified_at=item.original_modified_at
            )
            
            # Log the file creation
            self.logger.info(f"File created with ID: {file.id}")
            
            return f"Uploaded file: {item.path}"
                
        except Exception as e:
            self.logger.error(f"Error during file upload: {str(e)}")
            raise

    async def download_file(self, session: Session, path: str) -> Dict[str, str]:
        try:
            # First try to get file from database to see fast if it exists
            file = self.db_file_service.get_file(session, path)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Get file content from filesystem
            file_content = await self.file_system.read_file(file.path)

            return {
                "content": file_content,
                "filename": file.name,
                "created_at": file.original_created_at or file.created_at,
                "modified_at": file.original_modified_at or file.updated_at
            }
            
        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            raise

    async def delete_file(self, session: Session, path: str):
        try:
            file = self.db_file_service.get_file(session, path)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            # Delete from filesystem with idapt_data prefix
            await self.file_system.delete_file(path)
            
            # Delete from database
            result = self.db_file_service.delete_file(session, path)
            if not result:
                self.logger.warning(f"Failed to delete file from database for path: {path}")

            # Remove from LlamaIndex
            self.llama_index.delete_file(path)

        except Exception as e:
            self.logger.error(f"Error deleting file: {str(e)}")
            raise

    async def delete_folder(self, session: Session, path: str):
        try:
            folder = self.db_file_service.get_folder(session, path)
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")

            # Get all files in folder and subfolders recursively
            files, _ = self.db_file_service.get_folder_files_recursive(session, path)
            
            # Delete all files in the folder and subfolders
            for file in files:
                # Use our delete_file method to delete from filesystem and LlamaIndex
                await self.delete_file(session, file.path)

            # Delete folder and all subfolders from filesystem
            await self.file_system.delete_folder(folder.path)

            # Delete folder from database (will cascade delete files and subfolders)
            self.db_file_service.delete_folder(session, path)

        except Exception as e:
            self.logger.error(f"Error deleting folder: {str(e)}")
            raise

    async def rename_file(self, session: Session, path: str, new_name: str):
        try:
            file = self.db_file_service.get_file(session, path)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            # Rename in filesystem
            await self.file_system.rename_file(path, new_name)
            
            new_path = file.path.replace(file.name, new_name)
            # Update database
            updated_file = self.db_file_service.update_file(session, path, new_path)
            if not updated_file:
                raise HTTPException(status_code=500, detail="Failed to update file in database")

            # Update in LlamaIndex
            await self.llama_index.rename_file(old_path=path, new_path=new_path) 

        except Exception as e:
            self.logger.error(f"Error renaming file: {str(e)}")
            raise

    async def download_folder(self, session: Session, path: str) -> Dict[str, Any]:
        try:
            # Get folder from database
            folder = self.db_file_service.get_folder(session, path)
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            # Create a memory buffer for the zip file
            zip_buffer = BytesIO()
            
            # Create zip file
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Get all files recursively
                files, _ = self.db_file_service.get_folder_files_recursive(session, path)
                
                # Iterate over all retrieved files
                for file in files:
                    # Calculate relative path within the zip
                    relative_path = os.path.relpath(file.path, folder.path)
                    
                    # Read file content
                    file_content = await self.file_system.read_file(file.path)

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
            self.logger.error(f"Error creating folder zip: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating folder zip: {str(e)}")

    def get_folder_contents(self, session: Session, path: str | None) -> Tuple[List[File], List[Folder]]:
        """Get contents of a specific folder"""
        try:
            return self.db_file_service.get_folder_contents(session, path)
        except Exception as e:
            self.logger.error(f"Error getting folder contents: {str(e)}")
            raise
                    
    def preprocess_base64_file(self, base64_content: str) -> Tuple[bytes, str | None]:
        """ Decode base64 file content and return the file data and extension """
        try:
            header, data = base64_content.split(",", 1)
            mime_type = header.split(";")[0].split(":", 1)[1]
            extension = mimetypes.guess_extension(mime_type).lstrip(".")
            # File data as bytes
            return base64.b64decode(data), extension
        except Exception as e:
            self.logger.error(f"Error preprocessing base64 file: {str(e)}")
            raise