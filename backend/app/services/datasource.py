from sqlalchemy.orm import Session
from app.database.models import Datasource, Folder
from app.services.database import DatabaseService
from app.services.db_file import DBFileService
from app.services.file_manager import FileManagerService
from app.services.file_system import get_full_path_from_path
import logging
from typing import List, Optional

class DatasourceService:

    def __init__(self, database_service: DatabaseService, db_file_service: DBFileService, file_manager_service: FileManagerService):
        self.logger = logging.getLogger(__name__)
        self.database_service = database_service
        self.db_file_service = db_file_service
        self.file_manager_service = file_manager_service
        # Init the default datasource
        self._init_default_datasources(self.database_service.get_session())

    def _init_default_datasources(self, session: Session):
        """Initialize default datasources if they don't exist"""
        
        # Check if Files datasource exists
        if not self.get_datasource(session, "Files"):
            self.create_datasource(
                session=session,
                name="Files",
                type="files",
                settings={"description": "Default file storage"}
            ) 

    
    def create_datasource(self, session: Session, name: str, type: str, settings: dict = None) -> Datasource:
        """Create a new datasource with its root folder"""
        try:

            path = name
            # Create full path from datasource name
            full_path = get_full_path_from_path(path)

            # Get the folder id of the / folder
            root_folder_id = self.db_file_service.get_folder_id(session, "/data")

            # Create root folder for datasource
            datasource_folder = Folder(
                name=name,
                path=full_path,
                parent_id=root_folder_id  # Root level folder
            )
            session.add(datasource_folder)
            session.flush()  # Get the folder ID
            
            # Create datasource
            datasource = Datasource(
                name=name,
                type=type,
                settings=settings,
                root_folder_id=datasource_folder.id
            )
            session.add(datasource)
            session.commit()
            return datasource
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating datasource: {str(e)}")
            raise

    def get_datasource(self, session: Session, name: str) -> Optional[Datasource]:
        """Get a datasource by name"""
        return session.query(Datasource).filter(Datasource.name == name).first()

    def get_all_datasources(self, session: Session) -> List[Datasource]:
        """Get all datasources"""
        return session.query(Datasource).all()

    def delete_datasource(self, session: Session, name: str) -> bool:
        """Delete a datasource and its root folder"""
        datasource = self.get_datasource(session, name)
        if datasource:
            try:
                # Build full path from datasource name
                full_path = get_full_path_from_path(name)
                # Delete the datasource folder and all its contents both in the database and filesystem
                self.file_manager_service.delete_folder(session, full_path)
                # Delete the datasource
                session.delete(datasource)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error deleting datasource: {str(e)}")
                raise
        return False 