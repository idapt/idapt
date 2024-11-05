from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import create_engine
from app.database.models import File, Folder
from datetime import datetime
import mimetypes
import os
from typing import List


class DBFileService:
    @staticmethod
    def create_folder_path(session: Session, path: str) -> Folder:
        """Create folder hierarchy and return the last folder"""
        # Remove idapt_data from the start of the path if present
        path = path.replace('idapt_data/', '').replace('idapt_data\\', '')
        
        # Split path and filter out empty parts
        parts = [p for p in path.split('/') if p]
        current_folder = None
        
        print(f"Creating folder path: {path}")  # Debug log
        
        for part in parts:
            folder = session.query(Folder).filter(
                Folder.name == part,
                Folder.parent_id == (current_folder.id if current_folder else None)
            ).first()
            
            if not folder:
                print(f"Creating new folder: {part}")  # Debug log
                folder = Folder(
                    name=part,
                    parent_id=current_folder.id if current_folder else None
                    # TODO add original metadata support if uploaded ?
                )
                session.add(folder)
                session.commit()
            
            current_folder = folder
        
        return current_folder

    @staticmethod
    def create_file(        
        session: Session,
        name: str,
        folder_id: int | None = None,
        original_created_at: datetime | None = None,
        original_modified_at: datetime | None = None,
    ) -> File:
        """Create a file record in the database without content"""

        mime_type, _ = mimetypes.guess_type(name)
        
        file = File(
            name=name,
            mime_type=mime_type,
            folder_id=folder_id,
            original_created_at=original_created_at,
            original_modified_at=original_modified_at,
            # The following are automatically set by the database
            # created_at=datetime.utcnow(),
            # updated_at=datetime.utcnow()
        )
        
        session.add(file)
        session.commit()
        return file 

    @staticmethod
    def get_file_tree(session: Session) -> List[dict]:
        """Get complete file/folder hierarchy"""
        def build_tree(folder=None):
            query = session.query(Folder).filter(Folder.parent_id == (folder.id if folder else None))
            tree = []
            
            for folder in query.all():
                node = {
                    "id": folder.id,
                    "name": folder.name,
                    "type": "folder",
                    "children": build_tree(folder)
                }
                
                # Add files in this folder
                files = session.query(File).filter(File.folder_id == folder.id).all()
                node["children"].extend([{
                    "id": file.id,
                    "name": file.name,
                    "type": "file",
                    "mime_type": file.mime_type
                } for file in files])
                
                tree.append(node)
            
            return tree
        
        return build_tree()

    @staticmethod
    def get_folder_contents(session: Session, folder_id: int | None) -> List[dict]:
        folders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
        folder_nodes = [{
            "id": folder.id,
            "name": folder.name,
            "type": "folder",
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "original_created_at": folder.original_created_at,
            "original_modified_at": folder.original_modified_at
        } for folder in folders]

        # Get files - for root folder (folder_id is None) or specific folder
        files = session.query(File).filter(File.folder_id == folder_id).all()
        file_nodes = [{
            "id": file.id,
            "name": file.name,
            "type": "file",
            "mime_type": file.mime_type,
            "created_at": file.created_at,
            "updated_at": file.updated_at,
            "original_created_at": file.original_created_at,
            "original_modified_at": file.original_modified_at
        } for file in files]

        return folder_nodes + file_nodes

    @staticmethod
    def get_file(session: Session, file_id: int) -> File | None:
        """Get a file by ID"""
        return session.query(File).filter(File.id == file_id).first()

    @staticmethod
    def get_folder(session: Session, folder_id: int) -> Folder | None:
        """Get a folder by ID"""
        return session.query(Folder).filter(Folder.id == folder_id).first()

    @staticmethod
    def get_folder_files(session: Session, folder_id: int) -> List[File]:
        """Get all files in a folder"""
        return session.query(File).filter(File.folder_id == folder_id).all()

    @staticmethod
    def delete_file(session: Session, file_id: int) -> bool:
        """Delete a file from the database"""
        file = DBFileService.get_file(session, file_id)
        if file:
            session.delete(file)
            session.commit()
            return True
        return False

    @staticmethod
    def delete_folder(session: Session, folder_id: int) -> bool:
        """Delete a folder and all its files from the database"""
        folder = DBFileService.get_folder(session, folder_id)
        if folder:
            session.delete(folder)
            session.commit()
            return True
        return False

    @staticmethod
    def update_file(session: Session, file_id: int, name: str, path: str) -> File | None:
        """Update file name and path"""
        file = DBFileService.get_file(session, file_id)
        if file:
            file.name = name
            file.path = path
            file.updated_at = datetime.utcnow()
            session.commit()
            return file
        return None