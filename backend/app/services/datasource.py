from sqlalchemy.orm import Session
from app.database.models import Datasource, Folder
from app.services.db_file import get_db_folder_id
from app.services.file_manager import delete_folder
from app.services.file_system import get_full_path_from_path
from app.services.llama_index import get_storage_components, get_index, _delete_llama_index_components

import logging
from typing import List, Optional
import re

logger = logging.getLogger(__name__)


    # Storage components
    #self._vector_stores: Dict[str, ChromaVectorStore] = {}
    #self._doc_stores: Dict[str, SimpleDocumentStore] = {}
    #self._index_stores: Dict[str, SimpleIndexStore] = {}
    #self._indices: Dict[str, VectorStoreIndex] = {}
    #self._tools: Dict[str, BaseTool] = {}
    
    # Init the default datasource
    #with get_session() as session:
    #    _init_default_datasources(session)

def _init_default_datasources(session: Session):
    """Initialize default datasources if they don't exist"""
    try:
        if not get_datasource(session, "files"):
            create_datasource(
                session=session,
                name="Files",
                type="files",
                settings={}
            )
            logger.info("Created default datasource 'Files'")
            
    except Exception as e:
        logger.error(f"Error initializing default datasources: {str(e)}")
        raise

def create_datasource(session: Session, name: str, type: str, settings: dict = None) -> Datasource:
    """Create a new datasource with its root folder and all required components"""
    try:
        identifier = generate_identifier(name)
        # Check if the identifier is already used
        if get_datasource(session, identifier):
            raise ValueError(f"Datasource with identifier '{identifier}' already exists")

        path = identifier
        full_path = get_full_path_from_path(path)
        root_folder_id = get_db_folder_id(session, "/data")

        # Create root folder for datasource
        datasource_folder = Folder(
            name=name,  # Use display name for folder
            path=full_path,
            parent_id=root_folder_id
        )
        session.add(datasource_folder)
        session.flush()

        # Create datasource
        datasource = Datasource(
            identifier=identifier,  # Add identifier
            name=name,
            type=type,
            settings=settings,
            root_folder_id=datasource_folder.id
        )
        session.add(datasource)
        session.commit()

        # Initialize all llama-index components using identifier
        get_storage_components(identifier)
        get_index(identifier)

        return datasource
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating datasource: {str(e)}")
        raise

async def delete_datasource(session: Session, identifier: str) -> bool:
    """Delete a datasource and all its components"""
    try:
        datasource = get_datasource(session, identifier)
        if not datasource:
            return False

        # Store root folder reference before nullifying it
        root_folder = datasource.root_folder
        if not root_folder:
            raise Exception("Datasource has no root folder")
        
        root_folder_path = root_folder.path
        
        # First remove the root_folder reference from datasource
        datasource.root_folder_id = None
        session.flush()
        
        # Then try to delete all files and folders using the stored path
        try:
            await delete_folder(session, root_folder_path)
        except Exception as e:
            logger.error(f"Failed to delete datasource files and folders: {str(e)}")
            # Restore the root_folder_id reference since deletion failed
            datasource.root_folder_id = root_folder.id
            session.flush()
            raise Exception("Failed to delete datasource files. Please try again later.")

        # If file deletion succeeded, delete database entry
        session.delete(datasource)
        session.commit()

        # Delete llama-index components
        _delete_llama_index_components(session, identifier)
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting datasource: {str(e)}")
        raise


def get_datasource(session: Session, identifier: str) -> Optional[Datasource]:
    """Get a datasource by identifier"""
    return session.query(Datasource).filter(Datasource.identifier == identifier).first()

def get_all_datasources(session: Session) -> List[Datasource]:
    """Get all datasources"""
    return session.query(Datasource).all()

def update_datasource_description(session: Session, identifier: str, description: str) -> bool:
    """Update a datasource's description and its associated query tool"""
    try:
        datasource = get_datasource(session, identifier)
        if datasource:
            # Update description in database
            datasource.description = description
            session.commit()

            # Update the query tool description by recreating the tool
            # TODO Add caching

            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating datasource description: {str(e)}")
        raise
    
def get_datasource_identifier_from_path(path: str) -> str:
    """Get the datasource identifier from a path"""
    try:
        # Extract datasource name from path (first component after /data/)
        path_parts = path.split("/")
        data_index = path_parts.index("data")
        if data_index + 1 >= len(path_parts):
            raise ValueError(f"Invalid file path structure: {path}")
        return path_parts[data_index + 1]
    except Exception as e:
        # Do not use logger here
        raise ValueError(f"Invalid file path structure: {path}")

def generate_identifier(name: str) -> str:
    """Generate a safe identifier from a name"""
    try:
        # Convert to lowercase and replace spaces/special chars with underscores
        identifier = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        # Remove consecutive underscores
        identifier = re.sub(r'_+', '_', identifier)
        # Remove leading/trailing underscores
        identifier = identifier.strip('_')
        return identifier
    except Exception as e:
        # Do not use logger here
        raise ValueError(f"Invalid name: {name}")