from fastapi import HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import os
import base64
from typing import Dict, Any
import zipfile
import io

from app.services.db_file import DBFileService
from app.services.file_system import FileSystemService
from app.services.file import FileService
from app.api.routers.models import FileUploadItem
from app.services.llama_index import LlamaIndexService

class FileManagerService:
    def __init__(self):
        self.llama_index = LlamaIndexService()
        self.file_system = FileSystemService()
        self.file_service = FileService()

    async def process_upload_item(self, session: Session, item: FileUploadItem):
        """Process a single upload item (file or folder)"""
        try:
            if item.is_folder:
                # Create folder structure
                await self.file_system.create_folder(item.path)
                DBFileService.create_folder_path(session, item.path)
            else:
                # Process and save file
                file_data = base64.b64decode(item.content.split(',')[1])
                await self.file_system.save_file(item.path, file_data)
                
                # Create folder structure and file in database
                parent_path = str(Path(item.path).parent)
                folder = None if parent_path in ['', '.'] else DBFileService.create_folder_path(session, parent_path)
                
                DBFileService.create_file(
                    session=session,
                    name=item.name,
                    path=item.path,
                    folder_id=folder.id if folder else None,
                    original_created_at=item.original_created_at,
                    original_modified_at=item.original_modified_at,
                )
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

        # Delete from filesystem with idapt_data prefix
        await self.file_system.delete_file(f"/idapt_data/{file.path}")
        
        # Delete from database
        DBFileService.delete_file(session, file_id)

        # Remove from LlamaIndex
        await self.llama_index.remove_document(str(file_id))

    async def delete_folder(self, session: Session, folder_id: int):
        folder = DBFileService.get_folder(session, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Get all files in folder and subfolders recursively
        files = DBFileService.get_folder_files_recursive(session, folder_id)
        
        # Delete files from filesystem and LlamaIndex
        for file in files:
            await self.file_system.delete_file(file.path)
            await self.llama_index.remove_document(str(file.id))

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
            zip_buffer = io.BytesIO()
            
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