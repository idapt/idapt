import os
from pathlib import Path, PureWindowsPath
from fastapi import HTTPException
import shutil
import re
import uuid
from sqlalchemy.orm import Session

from app.api.user_path import get_user_data_dir
from app.database.models import File, Folder

import logging
logger = logging.getLogger('uvicorn')

async def write_file_filesystem(fs_path: str, content: bytes | str, created_at_unix_timestamp: float, modified_at_unix_timestamp: float):
    """Write content to a file in the filesystem and set its metadata"""
    try:
        fs_path = Path(fs_path)

        # Create parent directories if they don't exist
        if not fs_path.parent.exists():
            await create_folder_filesystem(str(fs_path.parent))
        
        if isinstance(content, str):
            content = content.encode()
            
        # Write the file content
        with open(str(fs_path), "wb") as f:
            f.write(content)

        # Set file timestamps
        # ! The file creation time will be set to the current time regardless of the value passed in
        os.utime(str(fs_path), (created_at_unix_timestamp, modified_at_unix_timestamp))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

async def read_file_filesystem(fs_path: str) -> bytes:
    """Read file from the filesystem"""
    try:
        with open(str(fs_path), "rb") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

async def create_folder_filesystem(fs_path: str):
    """Create a folder in the filesystem"""
    try:
        os.makedirs(str(fs_path), exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

async def delete_file_filesystem(fs_path: str):
    try:
        fs_path = Path(fs_path)
        if fs_path.exists():
            os.unlink(str(fs_path))
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

async def delete_folder_filesystem(fs_path: str):
    """Delete a folder and its contents from the filesystem"""
    try:
        fs_path = Path(fs_path)
        if fs_path.exists():
            shutil.rmtree(str(fs_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")

def get_fs_path_from_path(path: str, user_id: str) -> str:
    """Convert a relative path to a full path including user directory"""
    try:
        
        data_dir = Path(get_user_data_dir(user_id))
        
        if path == "" or path is None:
            return str(data_dir)
        
        path = Path(path)
        return str(data_dir / path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get full path from path: {str(e)}")

def get_path_from_fs_path(fs_path: str, user_id: str) -> str:
    """Convert a full filesystem path to a database path."""
    try:
        if fs_path is None or fs_path == "":
            return ""
        # Remove the user data directory from the full path
        user_data_dir = get_user_data_dir(user_id) + '/'
        path = fs_path.replace(user_data_dir, '')
        return path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get path from full path: {str(e)}")
    
def get_existing_fs_path_from_db(session: Session, original_path: str) -> str:
    """Get the existing fs path from the database"""
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
        raise HTTPException(status_code=400, detail=f"Failed to get existing fs path: {str(e)}")
    
def sanitize_name(name: str) -> str:
    """Sanitize a path name"""
    return re.sub(r'[^a-zA-Z0-9-_.]', '_', name)

def get_new_fs_path(original_path: str, user_id: str, session: Session, last_path_part_is_file : bool = True) -> str:
    """
    Sanitizes a path and ensures uniqueness for both original and fs paths.
    If the path exists in the database, it returns the existing path for consistency.
    It checks both files and folders in the database.
    Returns (sanitized_path, full_sanitized_path)
    """
    try:
        # Convert Windows path to Posix path if needed
        if '\\' in original_path:
            original_path = str(PureWindowsPath(original_path).as_posix())
        
        # Remove leading/trailing slashes and spaces
        clean_original_path = original_path.strip().strip('/')
        
        # TODO Add better error handling
        
        # Decompose the original path into into parts and for each part create a folder in the database if it doesn't exist
        original_path_parts = Path(clean_original_path).parts
        current_original_path = Path()
        current_sanitized_path = Path()
        for part_index in range(len(original_path_parts)):
                
            # Add the part to the current original path
            current_original_path = current_original_path / original_path_parts[part_index]

            
            # If the file already exists in the database with original path, we can use the fs path from the database
            existing_file = session.query(File).filter(File.original_path == str(current_original_path)).first()
            if existing_file:
                # Return the fs path from the database as this is the last part of the path
                # Raise an error as the file already exists and this function is for creating a new path
                raise HTTPException(status_code=400, detail=f"File already exists: {str(current_original_path)}")
                
            # If the folder already exists in the database at this original path, rebuild the current fs path from it and continue the loop
            existing_folder = session.query(Folder).filter(Folder.original_path == str(current_original_path)).first()
            if existing_folder:
                # Get its fs path and use it so that we keep things consistent and dont risk creating a new folder with the same name
                # Use it as the fs path for the rest of the loop as it contains the full right path up to this point
                current_sanitized_path = Path(existing_folder.path) 
                # Continue the loop as we dont need to create the folder in the database
                continue

            # Get the parent folder id from the database
            current_parent_original_path = "" if part_index == 0 else current_original_path.parent
            parent_folder = session.query(Folder).filter(Folder.original_path == str(current_parent_original_path)).first()
            if not parent_folder:
                raise ValueError(f"Parent folder {str(current_parent_original_path)} not found")
            
            # Build the fs path for the existing parent folder path that is already created and fs and add the current fs name to it
            current_sanitized_path = Path(parent_folder.path) / sanitize_name(original_path_parts[part_index])
            # Check if the fs path exists in the database and we need to generate a new unique fs path by appending a UUID to the end of the path
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
                        # We then exit the loop as it is the last part of the path and we have found a unique path
                    
                        #return current_sanitized_path_str
                    else:
                        # If it is a folder
                        current_sanitized_path = Path(str(base_current_sanitized_path.parent) + '/' + sanitize_name(original_path_parts[part_index]) + f"_{str(uuid.uuid4())[:8]}")
                    
                        
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