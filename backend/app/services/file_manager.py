from fastapi import HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import os
from typing import Dict

from app.services.db_file import DBFileService
from app.services.file_system import FileSystemService
from app.services.llama_index import LlamaIndexService

class FileManagerService:
    def __init__(self):
        self.file_system = FileSystemService()
        self.llama_index = LlamaIndexService()

    async def download_file(self, session: Session, file_id: int) -> Dict[str, str]:
        file = DBFileService.get_file(session, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
            
        file_path = Path(os.getenv("STORAGE_PATH", "")) / file.path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
            
        return {
            "path": str(file_path),
            "filename": file.name
        }

    async def delete_file(self, session: Session, file_id: int):
        file = DBFileService.get_file(session, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete from filesystem
        await self.file_system.delete_file(file.path)
        
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