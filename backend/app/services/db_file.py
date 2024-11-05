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
        path = path.replace('idapt_data/', '').replace('idapt_data\\', '')
        parts = [p for p in path.split('/') if p]
        current_folder = None
        current_path = ""
        
        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part
            
            # First try to find an existing folder with the same path
            folder = session.query(Folder).filter(
                Folder.path == current_path
            ).first()
            
            # If not found, try to find by name and parent
            if not folder:
                folder = session.query(Folder).filter(
                    Folder.name == part,
                    Folder.parent_id == (current_folder.id if current_folder else None)
                ).first()
            
            if not folder:
                print(f"Creating new folder: {part} with path {current_path}")
                folder = Folder(
                    name=part,
                    path=current_path,
                    parent_id=current_folder.id if current_folder else None
                )
                session.add(folder)
                try:
                    session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"Error creating folder: {str(e)}")
                    raise
            
            current_folder = folder
        
        return current_folder

    @staticmethod
    def create_file(
        session: Session,
        name: str,
        path: str,
        folder_id: int | None = None,
        original_created_at: datetime | None = None,
        original_modified_at: datetime | None = None,
    ) -> File:
        """Create a file record in the database without content"""
        try:
            mime_type, _ = mimetypes.guess_type(name)
            
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
            print(f"Error creating file: {str(e)}")
            raise
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
        """Delete a folder and all its contents from the database"""
        folder = DBFileService.get_folder(session, folder_id)
        if folder:
            try:
                # Delete all files in this folder and subfolders recursively
                files = DBFileService.get_folder_files_recursive(session, folder_id)
                for file in files:
                    session.delete(file)
                
                # Delete all subfolders recursively
                def delete_subfolders(folder_id):
                    subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
                    for subfolder in subfolders:
                        delete_subfolders(subfolder.id)
                        session.delete(subfolder)
                
                delete_subfolders(folder_id)
                
                # Delete the main folder
                session.delete(folder)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error deleting folder: {str(e)}")
                return False
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

    @staticmethod
    def get_folder_files_recursive(session: Session, folder_id: int) -> List[File]:
        """Get all files in a folder and its subfolders recursively"""
        # Get direct files in this folder
        files = session.query(File).filter(File.folder_id == folder_id).all()
        
        # Get all subfolders
        subfolders = session.query(Folder).filter(Folder.parent_id == folder_id).all()
        
        # Recursively get files from subfolders
        for subfolder in subfolders:
            files.extend(DBFileService.get_folder_files_recursive(session, subfolder.id))
        
        return files

    @staticmethod
    def path_exists(session: Session, path: str) -> bool:
        """Check if a file or folder exists at the given path"""
        file_exists = session.query(File).filter(File.path == path).first() is not None
        folder_exists = session.query(Folder).filter(Folder.path == path).first() is not None
        return file_exists or folder_exists