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
        # Check if root folder exists
        root_folder = session.query(Folder).filter(Folder.path == "/").first()
        if not root_folder:
            root_folder = Folder(
                name="root",
                path="/",
                parent_id=None
            )
            session.add(root_folder)
            session.flush()  # Flush to get the root_folder.id
            logger.info("Created default root folder in database")
        # Check if data folder exists
        data_folder = session.query(Folder).filter(Folder.path == "/data").first()
        if not data_folder:
            data_folder = Folder(
                name="data",
                path="/data",
                parent_id=root_folder.id
            )
            session.add(data_folder)
            session.flush()
            logger.info("Created default data folder in database")

        # Check if user folder exists
        user_folder_full_path = get_user_data_dir(user_id)
        user_folder = session.query(Folder).filter(Folder.path == user_folder_full_path).first()
        if not user_folder:
            user_folder = Folder(
                name=user_id,
                path=user_folder_full_path,
                parent_id=data_folder.id
            )
            session.add(user_folder)
            session.flush()
            logger.info(f"Created default user folder in database for user {user_id}")

        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default filestructure: {str(e)}")
        raise


def create_db_folder_path(session: Session, full_path: str) -> Folder:
    """Create folder hierarchy and return the last folder"""
    # Convert to Path object and make absolute
    path = Path(full_path).absolute()
    
    # Get all parts of the path
    parts = path.parts
    
    current_folder = None
    current_path = Path()
    
    # For each part of the path
    for part in parts:
        # Build the current path incrementally
        current_path = current_path / part
        current_path_str = str(current_path)
        
        # First try to find an existing folder with the same path in the database
        folder = session.query(Folder).filter(
            Folder.path == current_path_str
        ).first()
        
        # If not found, try to find by name and parent
        if not folder:
            folder = session.query(Folder).filter(
                Folder.name == part,
                Folder.parent_id == (current_folder.id if current_folder else None)
            ).first()
        
        # If not found, create a new folder
        if not folder:
            logger.info(f"Creating new folder: {part} with path {current_path_str}")
            folder = Folder(
                name=part,
                path=current_path_str,
                parent_id=current_folder.id if current_folder else None,
            )
            session.add(folder)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error creating folder: {str(e)}")
                raise
        
        # Set the current folder to the new folder, and continue with the next part of the path
        current_folder = folder
    
    # Return the last folder created, the one at the end of the path
    return current_folder

def create_db_file(
    session: Session,
    name: str,
    path: str,
    file_created_at: float,
    file_modified_at: float,
    size: int
) -> File:
    """Create a file record in the database without content"""
    try:
        # Guess the file mime type
        mime_type, _ = mimetypes.guess_type(name)

        # If there is a parent folder, create it, else get its id
        folder_id = None
        if path.count('/') >= 1:
            parent_path = str(Path(path).parent)
            folder_id = create_db_folder_path(session, parent_path).id
        else:
            folder_id = None # Root folder

        file = File(
            name=name,
            path=path,
            mime_type=mime_type,
            size=size,
            folder_id=folder_id,
            # Store timestamps in UTC datetime into the database as sqlalchemy need a datetime object
            file_created_at=datetime.fromtimestamp(file_created_at, tz=timezone.utc),
            file_modified_at=datetime.fromtimestamp(file_modified_at, tz=timezone.utc),
            # By default mark the file for processing with the default sentence splitter stack
            status=FileStatus.QUEUED,
            processed_stacks=json.dumps([]),
            stacks_to_process=json.dumps([])
        )
        
        session.add(file)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating file: {str(e)}")
        raise
    return file

def get_db_folder_contents(session: Session, full_path: str) -> Tuple[List[File], List[Folder]]:

    # Get folder id from path
    folder_id = get_db_folder_id(session, full_path)

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
