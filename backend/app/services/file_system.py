import os
from pathlib import Path
from fastapi import HTTPException
import shutil

from app.config import DATA_DIR

async def write_file_filesystem(full_path: str, content: bytes | str, created_at_unix_timestamp: float, modified_at_unix_timestamp: float):
    """Write content to a file in the filesystem and set its metadata"""
    try:
        full_path = Path(full_path)

        # Create parent directories if they don't exist
        if not full_path.parent.exists():
            os.makedirs(str(full_path.parent), exist_ok=True)
        
        if isinstance(content, str):
            content = content.encode()
            
        # Write the file content
        with open(str(full_path), "wb") as f:
            f.write(content)

        # Set file timestamps
        # ! The file creation time will be set to the current time regardless of the value passed in
        os.utime(str(full_path), (created_at_unix_timestamp, modified_at_unix_timestamp))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

async def read_file_filesystem(full_path: str) -> bytes:
    """Read file from the filesystem"""
    try:
        with open(str(full_path), "rb") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

async def create_folder_filesystem(full_path: str):
    """Create a folder in the filesystem"""
    try:
        os.makedirs(str(full_path), exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

async def delete_file_filesystem(full_path: str):
    try:
        full_path = Path(full_path)
        if full_path.exists():
            os.unlink(str(full_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

async def rename_file_filesystem(full_old_path: str, new_file_name: str) -> str:
    try:
        full_old_path = Path(full_old_path)
        directory = full_old_path.parent
        new_path = directory / new_file_name
        os.rename(str(full_old_path), str(new_path))
        return str(new_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename file: {str(e)}")

async def delete_folder_filesystem(full_path: str):
    """Delete a folder and its contents from the filesystem"""
    try:
        full_path = Path(full_path)
        if full_path.exists():
            shutil.rmtree(str(full_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")

def get_full_path_from_path(path: str) -> str:
    """Convert frontend path to backend full path"""
    # Remove any leading/trailing slashes from the path
    cleaned_path = path.strip('/')
    # If path is empty, return DATA_DIR
    if not cleaned_path:
        return DATA_DIR
    # Join the paths using os.path.join to handle slashes correctly
    return os.path.join(DATA_DIR, cleaned_path)

def get_path_from_full_path(full_path: str) -> str:
    """Convert a full filesystem path to a database path."""
    try:
        if full_path is None or full_path == "":
            return ""
        # Remove the DATA_DIR from the full path
        return full_path.replace(DATA_DIR, "") #str(Path(full_path).relative_to(DATA_DIR))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get path from full path: {str(e)}")
