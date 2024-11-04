from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.database.models import File, Folder
from app.database.connection import get_connection_string
from datetime import datetime
import mimetypes
import os
from typing import List

def get_db_session():
    engine = create_engine(get_connection_string())
    return Session(engine)

class DBFileService:
    @staticmethod
    def create_folder_path(session: Session, path: str) -> Folder:
        """Create folder hierarchy and return the last folder"""
        # Remove idapt_data from the start of the path if present
        path = path.replace('idapt_data/', '').replace('idapt_data\\', '')
        
        parts = [p for p in path.split('/') if p]
        current_folder = None
        
        for part in parts:
            folder = session.query(Folder).filter(
                Folder.name == part,
                Folder.parent_id == (current_folder.id if current_folder else None)
            ).first()
            
            if not folder:
                folder = Folder(
                    name=part,
                    parent_id=current_folder.id if current_folder else None
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
        file_type: str | None = None,
    ) -> File:
        """Create a file record in the database without content"""
        if not file_type:
            _, file_type = os.path.splitext(name)
            file_type = file_type.lstrip('.')
        
        mime_type, _ = mimetypes.guess_type(name)
        
        file = File(
            name=name,
            file_type=file_type,
            mime_type=mime_type,
            folder_id=folder_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
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
    def get_folder_contents(session: Session, folder_id: int | None = None) -> List[dict]:
        """Get contents of a specific folder or root folder if folder_id is None"""
        if folder_id is None:
            # If folder_id is None, return the contents of the root folder
            folders = session.query(Folder).filter(Folder.parent_id == None).all()
        else:
            # Get subfolders
            folders = session.query(Folder).filter(Folder.parent_id == folder_id).all()

        folder_nodes = [{
            "id": folder.id,
            "name": folder.name,
            "type": "folder"
        } for folder in folders]
        
        # Get files
        files = session.query(File).filter(File.folder_id == folder_id).all() if folder_id else session.query(File).filter(File.folder_id == None).all()
        file_nodes = [{
            "id": file.id,
            "name": file.name,
            "type": "file",
            "mime_type": file.mime_type
        } for file in files]
        
        return folder_nodes + file_nodes