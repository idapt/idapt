import os
from pathlib import Path, PureWindowsPath
from fastapi import HTTPException
import shutil
import re
import uuid
from typing import Tuple
from sqlalchemy.orm import Session

from app.services.user_path import get_user_data_dir
from app.database.models import File, Datasource

import logging
logger = logging.getLogger('uvicorn')

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

def get_full_path_from_path(path: str, user_id: str) -> str:
    """Convert a relative path to a full path including user directory"""
    return str(Path(get_user_data_dir(user_id), path.lstrip("/")))

def get_path_from_full_path(full_path: str, user_id: str) -> str:
    """Convert a full filesystem path to a database path."""
    try:
        if full_path is None or full_path == "":
            return ""
        # Remove the DATA_DIR from the full path
        return full_path.replace(get_user_data_dir(user_id), "") #str(Path(full_path).relative_to(DATA_DIR))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get path from full path: {str(e)}")

def validate_path(relative_path_from_home: str, session: Session) -> None:
    """Validate path format and security"""
    try:
        if not relative_path_from_home:
            raise HTTPException(status_code=400, detail="File path cannot be empty")
        
        if len(relative_path_from_home) > 255:
            raise HTTPException(status_code=400, detail="File name exceeds maximum length of 255 characters")

        # Check for invalid characters in filename
        invalid_chars = '<>:"|?*\\'
        if any(char in relative_path_from_home for char in invalid_chars):
            raise HTTPException(
                status_code=400,
                detail=f"File path contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )
        
        # Check if the path is relative and doesn't start with a /
        if relative_path_from_home.startswith('/'):
            raise HTTPException(status_code=400, detail="Path must be relative to the user's home directory")
        
        # Split path and validate datasource identifier
        path_parts = relative_path_from_home.split('/')
        if len(path_parts) < 1:
            raise HTTPException(
                status_code=400, 
                detail="Invalid path format. Path must include datasource identifier (e.g., 'files/your-file.txt')"
            )
            
        datasource_identifier = path_parts[0]  # Changed from [1] to [0]
        logger.info(f"Datasource identifier: {datasource_identifier}")
        
        # Check if datasource exists
        datasource = session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
        if datasource_identifier == '.idapt' or not datasource:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid datasource identifier '{datasource_identifier}'. Create a datasource first or use a valid datasource identifier"
            )
        
        # Check for path traversal attempts
        if '..' in relative_path_from_home or '//' in relative_path_from_home:
            raise HTTPException(
                status_code=400,
                detail="Invalid path: potential path traversal detected"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Path validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path format: {str(e)}"
        )

def sanitize_path(original_path: str, user_id: str, session: Session) -> Tuple[str, str]:
    """
    Sanitizes a path and ensures uniqueness for both original and sanitized paths.
    Returns (sanitized_path, full_sanitized_path)
    """
    try:
        # Convert Windows path to Posix path if needed
        if '\\' in original_path:
            original_path = str(PureWindowsPath(original_path).as_posix())
        
        # Remove leading/trailing slashes and spaces
        clean_path = original_path.strip().strip('/')
        
        # Basic path sanitization
        # Replace invalid chars with underscore, preserve extensions
        path_parts = clean_path.split('/')
        sanitized_parts = []
        
        for part in path_parts:
            if part:
                # Preserve the file extension if it's the last part
                if part == path_parts[-1] and '.' in part:
                    name, ext = os.path.splitext(part)
                    sanitized_name = re.sub(r'[^a-zA-Z0-9-_.]', '_', name)
                    sanitized_parts.append(f"{sanitized_name}{ext}")
                else:
                    sanitized_parts.append(re.sub(r'[^a-zA-Z0-9-_.]', '_', part))
        
        sanitized_path = '/'.join(sanitized_parts)
        
        # Check if original path exists
        existing_file = session.query(File).filter(File.original_path == original_path).first()
        if existing_file:
            # Return the existing sanitized path if we're overwriting
            return get_path_from_full_path(existing_file.path, user_id), existing_file.path
        
        # If not overwriting, check for path conflicts
        base_full_path = get_full_path_from_path(sanitized_path, user_id)
        full_path = base_full_path
        
        # If sanitized path exists (but not the original), append UUID until we find a unique path
        counter = 1
        while session.query(File).filter(File.path == full_path).first():
            # Split path into name and extension
            base_name, ext = os.path.splitext(base_full_path)
            full_path = f"{base_name}_{str(uuid.uuid4())[:8]}{ext}"
            counter += 1
            if counter > 100:  # Safeguard against infinite loops
                raise ValueError("Could not generate unique path after 100 attempts")
        
        return sanitized_path, full_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sanitize path: {str(e)}")