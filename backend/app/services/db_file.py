from sqlalchemy.orm import Session
from app.database.models import File, Folder
from datetime import datetime
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
    
    def create_folder_path(self, session: Session, path: str) -> Folder:
        """Create folder hierarchy and return the last folder"""
        # Split the path into parts
        parts = [p for p in path.split('/') if p]
    
        current_folder = None
        current_path = ""
        
        # For each part of the path
        for part in parts:
            # Build the current path from the parts and the current path, works because we start with the left first part
            current_path = f"{current_path}/{part}" if current_path else part
            
            # First try to find an existing folder with the same path in the database
            folder = session.query(Folder).filter(
                Folder.path == current_path
            ).first()
            
            # If not found, try to find by name and parent
            if not folder:
                folder = session.query(Folder).filter(
                    Folder.name == part,
                    Folder.parent_id == (current_folder.id if current_folder else None)
                ).first()
            
            # If not found, create a new folder
            if not folder:
                self.logger.info(f"Creating new folder: {part} with path {current_path}")
                folder = Folder(
                    name=part,
                    path=current_path,
                    parent_id=current_folder.id if current_folder else None,
                    original_created_at=datetime.now(), #Dummy values
                    original_modified_at=datetime.now()
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
        original_created_at: datetime | None = None,
        original_modified_at: datetime | None = None,
    ) -> File:
        """Create a file record in the database without content"""
        try:
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
                folder_id=folder_id,
                original_created_at=original_created_at,
                original_modified_at=original_modified_at,
            )
            
            session.add(file)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating file: {str(e)}")
            raise
        return file

    def get_folder_contents(self, session: Session, path: str | None) -> Tuple[List[File], List[Folder]]:
        
        folder_id = None
        # If path is not None, get folder id from path
        if path:
            folder_id = self.get_folder_id(session, path)

        # Get all folders in this folder
        folders = session.query(Folder).filter(Folder.parent_id == folder_id).all()

        # Get files - for root folder (folder_id is None) or specific folder
        files = session.query(File).filter(File.folder_id == folder_id).all()
        
        return files, folders

    def get_file(self, session: Session, path: str) -> File | None:
        """Get a file by ID"""
        return session.query(File).filter(File.path == path).first()

    def get_folder(self, session: Session, path: str) -> Folder | None:
        """Get a folder by ID"""
        return session.query(Folder).filter(Folder.path == path).first()

    def delete_file(self, session: Session, path: str) -> bool:
        """Delete a file from the database"""
        file = self.get_file(session, path)
        if file:                
            # Then delete from database
            session.delete(file)
            session.commit()
            return True
        return False

    def delete_folder(self, session: Session, path: str) -> bool:
        """Delete a folder and all its contents from the database"""
        # Get the folder from the database
        folder = self.get_folder(session, path)
        # If the folder exists
        if folder:
            try:
                # Delete all files in this folder and subfolders recursively
                files, _ = self.get_folder_files_recursive(session, path)
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
    

    def update_file(self, session: Session, old_path: str, new_path: str) -> File | None:
        """Update file name and path"""
        # Get the file from the database
        file = self.get_file(session, old_path)
        # If the file exists
        if file:
            # Get filename from new path
            name = Path(new_path).name

            # Update the file name and path
            file.name = name
            file.path = new_path
            file.updated_at = datetime.now(datetime.timezone.utc)
            # Commit the changes to the database
            session.commit()
            # Return the updated file
            return file
        # If the file does not exist, return None
        return None

    def get_folder_files_recursive(self, session: Session, path: str) -> Tuple[List[File], List[Folder]]:
        """Get all files in a folder and its subfolders recursively"""

        # Get folder id from path
        folder_id = self.get_folder_id(session, path)

        # Get direct files in this folder
        files = session.query(File).filter(File.folder_id == folder_id).all()
        
        # Get all subfolders
        subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
        
        # Recursively get files from subfolders
        for subfolder in subfolders:
            files.extend(self.get_folder_files_recursive(session, subfolder.id))
        
        return files, subfolders

    def get_file_id(self, session: Session, path: str) -> int | None:
        """Get the ID of a file by path"""
        file = session.query(File).filter(File.path == path).first()
        return file.id if file else None
    
    def get_folder_id(self, session: Session, path: str) -> int | None:
        """Get the ID of a folder by path"""
        folder = session.query(Folder).filter(Folder.path == path).first()
        return folder.id if folder else None
