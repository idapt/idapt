import os
from pathlib import Path
from fastapi import HTTPException
import shutil

class FileSystemService:
    def __init__(self):
        self.base_path = Path(os.getenv("STORAGE_PATH", ""))

    async def delete_file(self, file_path: str):
        try:
            full_path = self.base_path / file_path
            if full_path.exists():
                os.unlink(str(full_path))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    async def rename_file(self, old_path: str, new_name: str) -> str:
        try:
            full_old_path = self.base_path / old_path
            directory = full_old_path.parent
            new_path = directory / new_name
            os.rename(str(full_old_path), str(new_path))
            return str(new_path.relative_to(self.base_path))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to rename file: {str(e)}")

    async def delete_folder(self, folder_path: str):
        """Delete a folder and its contents from the filesystem"""
        full_path = Path(os.getenv("STORAGE_PATH", "")) / folder_path
        if full_path.exists():
            shutil.rmtree(str(full_path))