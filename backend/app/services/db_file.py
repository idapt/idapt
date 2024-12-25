from sqlalchemy.orm import Session
from app.database.models import File, Folder, FileStatus
from datetime import datetime, timezone
import mimetypes
import logging
from typing import List, Tuple
from pathlib import Path

class DBFileService:
    """
    Service for managing files and folders in the database
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def create_folder_path(self, session: Session, full_path: str) -> Folder:
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
                self.logger.info(f"Creating new folder: {part} with path {current_path_str}")
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
                    self.logger.error(f"Error creating folder: {str(e)}")
                    raise
            
            # Set the current folder to the new folder, and continue with the next part of the path
            current_folder = folder
        
        # Return the last folder created, the one at the end of the path
        return current_folder

    def create_file(
        self,
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
                folder_id = self.create_folder_path(session, parent_path).id
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
            )
            
            session.add(file)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating file: {str(e)}")
            raise
        return file

    def get_folder_contents(self, session: Session, full_path: str) -> Tuple[List[File], List[Folder]]:

        # Get folder id from path
        folder_id = self.get_folder_id(session, full_path)

        # Get all folders in this folder
        folders = session.query(Folder).filter(Folder.parent_id == folder_id).all()

        # Get files - for root folder (folder_id is None) or specific folder
        files = session.query(File).filter(File.folder_id == folder_id).all()
        
        return files, folders

    def get_file(self, session: Session, full_path: str) -> File | None:
        """Get a file by ID"""
        return session.query(File).filter(File.path == full_path).first()

    def get_folder(self, session: Session, full_path: str) -> Folder | None:
        """Get a folder by ID"""
        return session.query(Folder).filter(Folder.path == full_path).first()

    def delete_file(self, session: Session, full_path: str) -> bool:
        """Delete a file from the database"""
        file = self.get_file(session, full_path)
        if file:                
            # Then delete from database
            session.delete(file)
            session.commit()
            return True
        return False

    def delete_folder(self, session: Session, full_path: str) -> bool:
        """Delete a folder and all its contents from the database"""
        # Get the folder from the database
        folder = self.get_folder(session, full_path)
        # If the folder exists
        if folder:
            try:
                # Delete all files in this folder and subfolders recursively
                files, _ = self.get_folder_files_recursive(session, full_path)
                # Delete all files in this folder
                for file in files:
                    session.delete(file)
                
                # Delete all subfolders recursively
                self.delete_subfolders(session, folder.id)
                
                # Delete the main folder
                session.delete(folder)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error deleting folder: {str(e)}")
                return False
        return False
    
    # Delete all subfolders recursively
    def delete_subfolders(self, session: Session, folder_id: int):
        subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
        for subfolder in subfolders:
            self.delete_subfolders(session, subfolder.id)
            session.delete(subfolder)
    

    def update_file(self, session: Session, full_old_path: str, full_new_path: str) -> File | None:
        """Update file name and path"""
        # Get the file from the database
        file = self.get_file(session, full_old_path)
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

    def get_folder_files_recursive(self, session: Session, full_path: str) -> Tuple[List[File], List[Folder]]:
        """Get all files in a folder and its subfolders recursively"""

        self.logger.error(f"Full path recursive: {full_path}")

        # Get folder id from path
        folder_id = self.get_folder_id(session, full_path)

        # Get direct files in this folder
        files = session.query(File).filter(File.folder_id == folder_id).all()
        
        # Get all subfolders
        subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
        
        # Recursively get files from subfolders
        for subfolder in subfolders:
            files.extend(self.get_folder_files_recursive(session, subfolder.path))
        
        return files, subfolders

    def get_file_id(self, session: Session, full_path: str) -> int | None:
        """Get the ID of a file by path"""
        file = session.query(File).filter(File.path == full_path).first()
        return file.id if file else None
    
    def get_folder_id(self, session: Session, full_path: str) -> int | None:
        """Get the ID of a folder by path"""
        folder = session.query(Folder).filter(Folder.path == full_path).first()
        return folder.id if folder else None

    def update_file_status(
        self,
        session: Session,
        file_path: str,
        status: FileStatus,
        message: str = None
    ) -> File:
        """Update file status and related timestamps"""
        file = self.get_file(session, file_path)
        if not file:
            raise ValueError(f"File not found: {file_path}")
            
        file.status = status
        file.status_message = message
        
        if status == FileStatus.PROCESSING:
            file.processing_started_at = datetime.now(timezone.utc)
        elif status in [FileStatus.COMPLETED, FileStatus.ERROR]:
            file.processing_completed_at = datetime.now(timezone.utc)
            
        session.commit()
        return file
        
    def get_files_by_status(
        self,
        session: Session,
        status: FileStatus
    ) -> List[File]:
        """Get all files with a specific status"""
        return session.query(File).filter(File.status == status).all()
