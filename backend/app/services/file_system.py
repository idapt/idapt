import os
from pathlib import Path
from fastapi import HTTPException
import shutil

class FileSystemService:
    def __init__(self):
        self.base_path = Path(os.getenv("STORAGE_PATH", ""))

    async def write_file(self, file_path: str, content: bytes | str):
        """Write content to a file in the filesystem"""
        try:
            full_path = self.base_path / file_path
            os.makedirs(str(full_path.parent), exist_ok=True)
            
            if isinstance(content, str):
                content = content.encode()
                
            with open(str(full_path), "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

    async def create_folder(self, folder_path: str):
        """Create a folder in the filesystem"""
        try:
            full_path = self.base_path / folder_path
            os.makedirs(str(full_path), exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

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
        try:
            full_path = self.base_path / folder_path
            if full_path.exists():
                shutil.rmtree(str(full_path))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")