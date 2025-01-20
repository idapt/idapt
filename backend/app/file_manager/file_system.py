import os
from pathlib import Path, PureWindowsPath
from fastapi import HTTPException
import shutil
import re
import uuid
from typing import Tuple
from sqlalchemy.orm import Session

from app.user.user_path import get_user_data_dir
from app.database.models import File, Datasource, Folder

import logging
logger = logging.getLogger('uvicorn')

async def write_file_filesystem(full_path: str, content: bytes | str, created_at_unix_timestamp: float, modified_at_unix_timestamp: float):
    """Write content to a file in the filesystem and set its metadata"""
    try:
        full_path = Path(full_path)

        # Create parent directories if they don't exist
        if not full_path.parent.exists():
            await create_folder_filesystem(str(full_path.parent))
        
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
    try:
        
        data_dir = Path(get_user_data_dir(user_id))
        
        if path == "" or path is None:
            logger.debug(f"Path is empty, returning data directory: {str(data_dir)}")
            return str(data_dir)
        
        path = Path(path)
        logger.debug(f"Path: {str(data_dir / path)}")
        return str(data_dir / path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get full path from path: {str(e)}")

def get_path_from_full_path(full_path: str, user_id: str) -> str:
    """Convert a full filesystem path to a database path."""
    try:
        if full_path is None or full_path == "":
            return ""
        # Remove the user data directory from the full path
        user_data_dir = get_user_data_dir(user_id) + '/'
        path = full_path.replace(user_data_dir, '')
        logger.debug(f"Path result: {path}")
        return path
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
            
        original_datasource_name = path_parts[0]
        logger.info(f"Datasource name: {original_datasource_name}")
        
        # Check if datasource exists
        datasource = session.query(Datasource).filter(Datasource.name == original_datasource_name).first()
        if original_datasource_name == '.idapt' or not datasource:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid datasource identifier '{original_datasource_name}'. Create a datasource first or use a valid datasource identifier"
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
    
def get_existing_sanitized_path(session: Session, original_path: str) -> str:
    """Get the existing sanitized path from the database"""
    try:
        # Check if the file exists in the database
        file = session.query(File).filter(File.original_path == original_path).first()
        if file:
            return file.path
        # Check if the folder exists in the database
        folder = session.query(Folder).filter(Folder.original_path == original_path).first()
        if folder:
            return folder.path
        raise HTTPException(status_code=404, detail=f"File or folder not found: {original_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get existing sanitized path: {str(e)}")
    
def sanitize_name(name: str) -> str:
    """Sanitize a path name"""
    return re.sub(r'[^a-zA-Z0-9-_.]', '_', name)

def get_new_sanitized_path(original_path: str, user_id: str, session: Session, last_path_part_is_file : bool = True) -> str:
    """
    Sanitizes a path and ensures uniqueness for both original and sanitized paths.
    If the path exists in the database, it returns the existing path for consistency.
    It checks both files and folders in the database.
    Returns (sanitized_path, full_sanitized_path)
    """
    try:
        logger.debug(f"Sanitizing path: {original_path}")
        # Convert Windows path to Posix path if needed
        if '\\' in original_path:
            original_path = str(PureWindowsPath(original_path).as_posix())
        
        # Remove leading/trailing slashes and spaces
        clean_original_path = original_path.strip().strip('/')
        
        # TODO Add better error handling
        
        # Decompose the original path into into parts and for each part create a folder in the database if it doesn't exist
        original_path_parts = Path(clean_original_path).parts
        logger.debug(f"Original path parts: {original_path_parts}")
        current_original_path = Path()
        current_sanitized_path = Path()
        for part_index in range(len(original_path_parts)):
                
            # Add the part to the current original path
            current_original_path = current_original_path / original_path_parts[part_index]

            
            # If the file already exists in the database with original path, we can use the sanitized path from the database
            existing_file = session.query(File).filter(File.original_path == str(current_original_path)).first()
            if existing_file:
                logger.debug(f"File already exists in the database with original path: {str(current_original_path)}")
                # Return the sanitized path from the database as this is the last part of the path
                # Raise an error as the file already exists and this function is for creating a new path
                raise HTTPException(status_code=400, detail=f"File already exists: {str(current_original_path)}")
                
            # If the folder already exists in the database at this original path, rebuild the current sanitized path from it and continue the loop
            existing_folder = session.query(Folder).filter(Folder.original_path == str(current_original_path)).first()
            if existing_folder:
                # Get its sanitized path and use it so that we keep things consistent and dont risk creating a new folder with the same name
                # Use it as the sanitized path for the rest of the loop as it contains the full right path up to this point
                current_sanitized_path = Path(existing_folder.path) 
                # Continue the loop as we dont need to create the folder in the database
                continue

            # Get the parent folder id from the database
            current_parent_original_path = "" if part_index == 0 else current_original_path.parent
            parent_folder = session.query(Folder).filter(Folder.original_path == str(current_parent_original_path)).first()
            if not parent_folder:
                raise ValueError(f"Parent folder {str(current_parent_original_path)} not found")
            
            # Build the sanitized path for the existing parent folder path that is already created and sanitized and add the current sanitized name to it
            current_sanitized_path = Path(parent_folder.path) / sanitize_name(original_path_parts[part_index])
            logger.debug(f"Current sanitized path: {current_sanitized_path}")
            # Check if the sanitized path exists in the database and we need to generate a new unique sanitized path by appending a UUID to the end of the path
            if session.query(File).filter(File.path == str(current_sanitized_path)).first() or session.query(Folder).filter(Folder.path == str(current_sanitized_path)).first():
                # Generate the uuid  
                base_current_sanitized_path = current_sanitized_path
                attempt = 0
                while attempt < 100:
                    logger.debug(f"Path {current_sanitized_path} is not unique, trying to generate a unique path")
                    attempt += 1
                    # Check if the path is unique
                    if not session.query(File).filter(File.path == str(current_sanitized_path)).first() and not session.query(Folder).filter(Folder.path == str(current_sanitized_path)).first():
                        break
                
                    # If we are at the last item of the path and if the last part is a file, we dont want to create a folder with the name of the file
                    if part_index == len(original_path_parts) - 1 and last_path_part_is_file:
                        # Do sanitize the name of the file minding the extension
                        # Split path into name and extension
                        base_name, ext = os.path.splitext(str(base_current_sanitized_path))
                        current_sanitized_path = Path(str(base_current_sanitized_path.parent) + '/' + base_name + '_' + str(uuid.uuid4())[:8] + ext)
                        logger.debug(f"Path already exists: {current_sanitized_path} trying {attempt} times to generate a unique path")
                        # We then exit the loop as it is the last part of the path and we have found a unique path
                    
                        #return current_sanitized_path_str
                    else:
                        # If it is a folder
                        
                        current_sanitized_path = Path(str(base_current_sanitized_path.parent) + '/' + sanitize_name(original_path_parts[part_index]) + f"_{str(uuid.uuid4())[:8]}")
                        logger.debug(f"Path already exists for folder: {current_sanitized_path} trying {attempt} times to generate a unique path")
                    
                        
                if attempt >= 100:
                    raise ValueError("Could not generate unique path after 100 attempts")
            
                                            
            # If we are at the last item of the path and if the last part is a file, we dont want to create a folder with the name of the file
            if part_index == len(original_path_parts) - 1 and last_path_part_is_file:
                return str(current_sanitized_path)

            # Create the folder in the database
            folder = Folder(
                name=original_path_parts[part_index],
                path=str(current_sanitized_path),
                original_path=str(current_original_path),
                parent_id=parent_folder.id
            )
            session.add(folder)
            session.flush()

            # We are at the last item of the path and it is a folder
            if part_index == len(original_path_parts) - 1:
                return str(current_sanitized_path) 
                
        # If we reach this point, something went wrong
        raise HTTPException(status_code=400, detail=f"Failed to sanitize path: {str(current_sanitized_path)}")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sanitize path: {str(e)}")