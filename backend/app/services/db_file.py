from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.database.models import File, Folder
from app.database.connection import get_connection_string
from datetime import datetime
import mimetypes
import os

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