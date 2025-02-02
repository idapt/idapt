from sqlalchemy.orm import Session
import logging
from typing import List, Tuple

from app.datasources.file_manager.database.models import File, Folder

logger = logging.getLogger("uvicorn")

def delete_db_folder_recursive(file_manager_session: Session, fs_path: str) -> bool:
    """Delete a folder and all its contents from the database"""
    # Get the folder from the database
    folder = file_manager_session.query(Folder).filter(Folder.path == fs_path).first()
    # If the folder exists
    if folder:
        try:
            # Delete all files in this folder and subfolders recursively
            # Get folder id from path
            folder_id = file_manager_session.query(Folder).filter(Folder.path == fs_path).first().id
            # Get all folders in this folder
            folders = file_manager_session.query(Folder).filter(Folder.parent_id == folder_id).all()
            # Get files - for root folder (folder_id is None) or specific folder
            files = file_manager_session.query(File).filter(File.folder_id == folder_id).all()
            # Delete all subfolders and thier content recursively
            for subfolder in folders:
                delete_db_folder_recursive(file_manager_session, subfolder.path)
            
            # Delete all files in this folder
            for file in files:
                file_manager_session.delete(file)
            
            # Delete this folder
            file_manager_session.delete(folder)
            
            # Commit everything at once
            file_manager_session.commit()
            return True
        except Exception as e:
            file_manager_session.rollback()
            logger.error(f"Error deleting folder: {str(e)}")
            return False
    return False

def get_db_folder_files_recursive(file_manager_session: Session, fs_path: str) -> Tuple[List[File], List[Folder]]:
    """Get all files in a folder and its subfolders recursively"""
    
    # Get folder id from path
    folder_id = file_manager_session.query(Folder).filter(Folder.path == fs_path).first().id

    # Get direct files in this folder
    files = file_manager_session.query(File).filter(File.folder_id == folder_id).all()
    
    # Get all subfolders
    subfolders = file_manager_session.query(Folder).filter(Folder.parent_id == folder_id).all()
    
    # Recursively get files from subfolders
    for subfolder in subfolders:
        subfolder_files, subfolder_folders = get_db_folder_files_recursive(file_manager_session, subfolder.path)
        files.extend(subfolder_files)
        subfolders.extend(subfolder_folders)
    
    return files, subfolders