import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.database.models import Datasource, Folder
from app.file_manager.service.service import delete_folder
from app.file_manager.service.file_system import get_fs_path_from_path, get_new_fs_path
from app.user.user_path import get_user_data_dir
from app.file_manager.service.llama_index import delete_datasource_llama_index_components, delete_files_in_folder_recursive_from_llama_index
from app.settings.schemas import OllamaEmbedSettings

import logging
from typing import List, Optional
import re



logger = logging.getLogger("uvicorn")

def init_default_datasources(session: Session, user_id: str):
    """Initialize default datasources if they don't exist"""
    try:
        if not get_datasource(session, "Files"):
            default_embedding_settings = OllamaEmbedSettings()
                        
            create_datasource(
                session=session,
                user_id=user_id,
                name="Files",
                type="files",
                description="Various files, prefer using another datasource if it seems more relevant",
                settings_json={},
                embedding_provider="ollama_embed",
                embedding_settings_json=json.dumps(default_embedding_settings.model_dump())
            )
            logger.info("Created default datasource 'Files'")
            
    except Exception as e:
        logger.error(f"Error initializing default datasources: {str(e)}")
        raise

def create_datasource(
    session: Session, 
    user_id: str, 
    name: str, 
    type: str,
    embedding_provider: str,
    embedding_settings_json: str,
    settings_json: str = None,
    description: Optional[str] = None
) -> Datasource:
    """Create a new datasource with its root folder and all required components"""
    try:
        # Check for invalid characters in name
        invalid_chars = '<>:"|?*\\'
        if any(char in name for char in invalid_chars):
            raise ValueError(
                f"Datasource name contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )
        
        # Check if the datasource name is valid
        if name == '.idapt':
            raise ValueError("Datasource name cannot be '.idapt'")

        # If the path already exists, the get_new_fs_path will append an uuid and get an unique path for it
        fs_path = get_new_fs_path(name, user_id, session, False)
        # Extract the fs datasource name as identifier from the full path last component
        identifier = Path(fs_path).name

        if settings_json is None:
            settings_json = {}

        if embedding_settings_json is None:
            embedding_settings_json = {}

        root_folder_path = get_user_data_dir(user_id)
        root_folder_id = session.query(Folder).filter(Folder.path == root_folder_path).first().id

        # Create root folder for datasource
        full_datasource_path = get_fs_path_from_path(identifier, user_id)
        # Try to get the folder from the database
        datasource_folder = session.query(Folder).filter(Folder.path == full_datasource_path).first()
        if not datasource_folder:
            # Create the folder in the database if it doesn't exist
            datasource_folder = Folder(
                name=name,
                path=full_datasource_path,
                original_path=name,
                parent_id=root_folder_id
            )
            session.add(datasource_folder)
            session.flush()
        else:
            logger.info(f"Datasource folder already exists: {datasource_folder.path}")

        # Create datasource with embedding settings
        datasource = Datasource(
            identifier=identifier,
            name=name,
            type=type,
            description=description,
            settings=settings_json,
            embedding_provider=embedding_provider,
            embedding_settings=embedding_settings_json,
            root_folder_id=datasource_folder.id
        )
        session.add(datasource)
        session.flush()  # This will populate the id field

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
        delete_datasource_llama_index_components(datasource.identifier, datasource.id, user_id)

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

async def update_datasource(session: Session, user_id: str, identifier: str, description: str, embedding_provider: str, embedding_settings: str) -> bool:
    """Update a datasource's description and its associated query tool"""
    try:
        datasource = get_datasource(session, identifier)

        if not datasource:
            return False
        # Convert embedding_settings to json string
        embedding_settings_json = json.dumps(embedding_settings)
        # If the provider has changed, delete the llama index components
        if datasource.embedding_provider != embedding_provider or datasource.embedding_settings != embedding_settings_json:
            # If there is 
            # Get root folder of datasource
            root_folder = session.query(Folder).filter(Folder.id == datasource.root_folder_id).first()
            if not root_folder:
                raise Exception("Datasource has no root folder")
            # Delete the files in the folder from llama index
            delete_files_in_folder_recursive_from_llama_index(session, user_id, root_folder.path)
            # Delete the datasource llama index components
            delete_datasource_llama_index_components(datasource.identifier, datasource.id, user_id)
            # New one will be created when first files are processed with it
            datasource.embedding_provider = embedding_provider
            datasource.embedding_settings = embedding_settings_json

        # Update description in database
        datasource.description = description
        session.commit()
    
        return True
    
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