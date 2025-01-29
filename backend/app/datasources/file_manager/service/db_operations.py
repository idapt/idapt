from sqlalchemy.orm import Session
import logging
from typing import List, Tuple

from app.api.user_path import get_user_data_dir
from app.datasources.file_manager.models import File, Folder

logger = logging.getLogger("uvicorn")
    
def create_default_db_filestructure_if_needed(session: Session, user_id: str):
    """Create the default filestructure in the database if needed"""
    try:
        # Check if user folder exists
        user_folder_fs_path = get_user_data_dir(user_id)
        user_folder = session.query(Folder).filter(Folder.path == user_folder_fs_path).first()
        if user_folder:
            return
        
        user_folder = Folder(
            name=user_id,
            path=user_folder_fs_path,
            original_path="",
            parent_id=None
        )
        session.add(user_folder)
        session.flush()
        logger.info(f"Created default user folder in database for user {user_id}")

        session.commit()

        logger.info("Default folders initialized")

            
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default filestructure: {str(e)}")
        raise

def delete_db_folder_recursive(session: Session, fs_path: str) -> bool:
    """Delete a folder and all its contents from the database"""
    # Get the folder from the database
    folder = session.query(Folder).filter(Folder.path == fs_path).first()
    # If the folder exists
    if folder:
        try:
            # Delete all files in this folder and subfolders recursively
            # Get folder id from path
            folder_id = session.query(Folder).filter(Folder.path == fs_path).first().id
            # Get all folders in this folder
            folders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
            # Get files - for root folder (folder_id is None) or specific folder
            files = session.query(File).filter(File.folder_id == folder_id).all()
            # Delete all subfolders and thier content recursively
            for subfolder in folders:
                delete_db_folder_recursive(session, subfolder.path)
            
            # Delete all files in this folder
            for file in files:
                session.delete(file)
            
            # Delete this folder
            session.delete(folder)
            
            # Commit everything at once
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting folder: {str(e)}")
            return False
    return False

def get_db_folder_files_recursive(session: Session, fs_path: str) -> Tuple[List[File], List[Folder]]:
    """Get all files in a folder and its subfolders recursively"""
    
    # Get folder id from path
    folder_id = session.query(Folder).filter(Folder.path == fs_path).first().id

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