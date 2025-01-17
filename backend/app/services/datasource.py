from sqlalchemy.orm import Session
from app.database.models import Datasource, Folder
from app.services.db_file import get_db_folder_id
from app.services.file_manager import delete_folder
from app.services.file_system import get_full_path_from_path
from app.services.user_path import get_user_data_dir
from app.services.llama_index import delete_datasource_llama_index_components

import logging
from typing import List, Optional
import re


logger = logging.getLogger("uvicorn")

def init_default_datasources(session: Session, user_id: str):
    """Initialize default datasources if they don't exist"""
    try:
        if not get_datasource(session, "files"):
            create_datasource(
                session=session,
                user_id=user_id,
                name="Files",
                type="files",
                settings={}
            )
            logger.info("Created default datasource 'Files'")
            
    except Exception as e:
        logger.error(f"Error initializing default datasources: {str(e)}")
        raise

def validate_datasource_name(name: str) -> tuple[bool, str]:
    """Validate datasource name according to Chroma requirements"""
    if len(name) < 3 or len(name) > 63:
        return False, "Name must be between 3 and 63 characters"
    
    if not name[0].isalnum() or not name[-1].isalnum():
        return False, "Name must start and end with an alphanumeric character"
        
    if '..' in name:
        return False, "Name cannot contain consecutive periods (..)"
        
    if not all(c.isalnum() or c in '_-.' for c in name):
        return False, "Name can only contain alphanumeric characters, underscores, hyphens or single periods"
        
    # Check if it's not an IPv4 address
    if all(part.isdigit() and 0 <= int(part) <= 255 for part in name.split('.')):
        return False, "Name cannot be in IPv4 address format"
        
    return True, ""

def create_datasource(session: Session, user_id: str, name: str, type: str, settings: dict = None) -> Datasource:
    """Create a new datasource with its root folder and all required components"""
    try:
        # Validate name first
        is_valid, error_message = validate_datasource_name(name)
        if not is_valid:
            raise ValueError(f"Invalid datasource name: {error_message}")

        identifier = generate_identifier(name)
        # Check if the identifier is already used
        if get_datasource(session, identifier):
            raise ValueError(f"Datasource with identifier '{identifier}' already exists")

        # Ensure settings is a dict
        if settings is None:
            settings = {}
        elif not isinstance(settings, dict):
            raise ValueError("Settings must be a dictionary")

        path = identifier
        root_folder_path = get_user_data_dir(user_id)
        root_folder_id = get_db_folder_id(session, root_folder_path)

        # Create root folder for datasource
        full_datasource_path = get_full_path_from_path(path, user_id)
        datasource_folder = Folder(
            name=name,
            path=full_datasource_path,
            parent_id=root_folder_id
        )
        session.add(datasource_folder)
        session.flush()

        # Create datasource
        datasource = Datasource(
            identifier=identifier,
            name=name,
            type=type,
            settings=settings,  # Now guaranteed to be a dict
            root_folder_id=datasource_folder.id
        )
        session.add(datasource)
        session.commit()

        return datasource
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating datasource: {str(e)}")
        raise

async def delete_datasource(session: Session, user_id: str, identifier: str) -> bool:
    """Delete a datasource and all its components"""
    # TODO Make more robust to avoid partial deletion
    try:
        datasource = get_datasource(session, identifier)
        if not datasource:
            return False

        # Store root folder reference before nullifying it
        root_folder = datasource.root_folder
        if not root_folder:
            raise Exception("Datasource has no root folder")
        
        root_folder_path = root_folder.path
        
        # First remove the root_folder reference from datasource to allow deletion of all files and folders of this datasource
        datasource.root_folder_id = None
        session.flush()
        
        # Then try to delete all files and folders using the stored path
        await delete_folder(session, user_id, root_folder_path)

        # Delete the llama index components
        delete_datasource_llama_index_components(identifier, user_id)

        # If file deletion succeeded, delete database entry
        session.delete(datasource)
        session.commit()

        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting datasource: {str(e)}")
        logger.error(f"Failed to delete datasource files and folders: {str(e)}")
        # Restore the root_folder_id reference since deletion failed
        datasource.root_folder_id = root_folder.id
        session.flush()
        raise Exception(f"Failed to delete datasource files. Please try again later : {str(e)}")
        

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
        if data_index + 2 >= len(path_parts):
            raise ValueError(f"Invalid file path structure: {path}")
        return path_parts[data_index + 2]
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