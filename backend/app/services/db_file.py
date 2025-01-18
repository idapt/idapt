import json
from sqlalchemy.orm import Session
from app.database.models import File, Folder, FileStatus
from datetime import datetime, timezone
import mimetypes
import logging
from typing import List, Tuple
from pathlib import Path
from app.services.user_path import get_user_data_dir

logger = logging.getLogger("uvicorn")
    
def create_default_db_filestructure(session: Session, user_id: str):
    """Create the default filestructure in the database"""
    try:
        # Check if user folder exists
        user_folder_full_path = get_user_data_dir(user_id)
        user_folder = session.query(Folder).filter(Folder.path == user_folder_full_path).first()
        if not user_folder:
            user_folder = Folder(
                name=user_id,
                path=user_folder_full_path,
                original_path="",
                parent_id=None
            )
            session.add(user_folder)
            session.flush()
            logger.info(f"Created default user folder in database for user {user_id}")

        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default filestructure: {str(e)}")
        raise

def get_db_folder_contents(session: Session, full_path: str) -> Tuple[List[File], List[Folder]]:

    # Get folder id from path
    folder_id = get_db_folder_id(session, full_path)

    if not folder_id:
        raise ValueError(f"Folder {full_path} not found")

    # Get all folders in this folder
    folders = session.query(Folder).filter(Folder.parent_id == folder_id).all()

    # Get files - for root folder (folder_id is None) or specific folder
    files = session.query(File).filter(File.folder_id == folder_id).all()
    
    return files, folders

def get_db_file(session: Session, full_path: str) -> File | None:
    """Get a file by ID"""
    return session.query(File).filter(File.path == full_path).first()

def get_db_folder(session: Session, full_path: str) -> Folder | None:
    """Get a folder by ID"""
    return session.query(Folder).filter(Folder.path == full_path).first()

def delete_db_file(session: Session, full_path: str) -> bool:
    """Delete a file from the database"""
    file = get_db_file(session, full_path)
    if file:                
        # Then delete from database
        session.delete(file)
        session.commit()
        return True
    return False

def delete_db_folder(session: Session, full_path: str) -> bool:
    """Delete a folder and all its contents from the database"""
    # Get the folder from the database
    folder = get_db_folder(session, full_path)
    # If the folder exists
    if folder:
        try:
            # Delete all files in this folder and subfolders recursively
            files, _ = get_db_folder_files_recursive(session, full_path)
            
            # Delete all files in a single transaction
            for file in files:
                session.delete(file)
            
            # Delete all subfolders recursively
            delete_subfolders(session, folder.id)
            
            # Delete the main folder
            session.delete(folder)
            
            # Commit everything at once
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting folder: {str(e)}")
            return False
    return False

# Delete all subfolders recursively
def delete_subfolders(session: Session, folder_id: int):
    subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
    for subfolder in subfolders:
        delete_subfolders(session, subfolder.id)
        session.delete(subfolder)


def update_db_file(session: Session, full_old_path: str, full_new_path: str) -> File | None:
    """Update file name and path"""
    # Get the file from the database
    file = get_db_file(session, full_old_path)
    # If the file exists
    if file:
        # Get filename from new path
        name = Path(full_new_path).name

        # Update the file name and path
        file.name = name
        file.path = full_new_path
        # Commit the changes to the database
        session.commit()
        # Return the updated file
        return file
    # If the file does not exist, return None
    return None

def get_db_folder_files_recursive(session: Session, full_path: str) -> Tuple[List[File], List[Folder]]:
    """Get all files in a folder and its subfolders recursively"""
    
    # Get folder id from path
    folder_id = get_db_folder_id(session, full_path)

    # Get direct files in this folder
    files = session.query(File).filter(File.folder_id == folder_id).all()
    
    # Get all subfolders
    subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
    
    # Recursively get files from subfolders
    for subfolder in subfolders:
        subfolder_files, subfolder_folders = get_db_folder_files_recursive(session, subfolder.path)
        files.extend(subfolder_files)
        subfolders.extend(subfolder_folders)
    
    return files, subfolders

def get_db_file_id(session: Session, full_path: str) -> int | None:
    """Get the ID of a file by path"""
    file = session.query(File).filter(File.path == full_path).first()
    return file.id if file else None

def get_db_folder_id(session: Session, full_path: str) -> int | None:
    """Get the ID of a folder by path"""
    folder = session.query(Folder).filter(Folder.path == full_path).first()
    return folder.id if folder else None

def get_db_files_by_status(
    session: Session,
    status: FileStatus
) -> List[File]:
    """Get all files with a specific status"""
    return session.query(File).filter(File.status == status).all()
