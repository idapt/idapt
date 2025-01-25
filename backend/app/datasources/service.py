import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.file_manager.models import Folder
from app.datasources.models import Datasource
from app.file_manager.service.service import delete_folder
from app.file_manager.service.file_system import get_new_fs_path
from app.api.user_path import get_user_data_dir
from app.file_manager.service.llama_index import delete_datasource_llama_index_components, delete_files_in_folder_recursive_from_llama_index
from app.datasources.schemas import DatasourceResponse, DatasourceUpdate, DatasourceCreate
from app.settings.schemas import get_embedding_provider_class
from app.settings.schemas import OllamaEmbedSettings

import logging
from typing import List, Optional
import re



logger = logging.getLogger("uvicorn")

def init_default_datasources_if_needed(session: Session, user_id: str):
    """Initialize default datasources if they don't exist"""
    try:
        
        if session.query(Datasource).filter(Datasource.name == "Files").first():
            return

        default_embedding_settings = OllamaEmbedSettings()
        datasource_create = DatasourceCreate(
            name="Files",
            type="files",
            description="Various files, prefer using another datasource if it seems more relevant",
            embedding_provider="ollama_embed",
            embedding_settings_json=default_embedding_settings.model_dump_json()
        )
        create_datasource(
            session=session,
            user_id=user_id,
            datasource_create=datasource_create
        )        
        logger.info("Default datasources initialized")

    except Exception as e:
        logger.error(f"Error initializing default datasources: {str(e)}")
        raise

def create_datasource(
    session: Session, 
    user_id: str, 
    datasource_create: DatasourceCreate
) -> None:
    """Create a new datasource with its root folder and all required components"""
    try:
        # Check for invalid characters in name
        invalid_chars = '<>:"|?*\\'
        if any(char in datasource_create.name for char in invalid_chars):
            raise ValueError(
                f"Datasource name contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )
        
        # Check if the datasource name is valid
        if datasource_create.name == '.idapt':
            raise ValueError("Datasource name cannot be '.idapt'")
        
        # Check if datasource with this name already exists
        if session.query(Datasource).filter(Datasource.name == datasource_create.name).first():
            raise ValueError(f"Datasource with name '{datasource_create.name}' already exists")

        # If the path already exists, the get_new_fs_path will append an uuid and get an unique path for it
        fs_datasource_path = get_new_fs_path(original_path=datasource_create.name, session=session, last_path_part_is_file=False)
        # Extract the fs datasource name as identifier from the full path last component
        identifier = Path(fs_datasource_path).name

        root_folder_path = get_user_data_dir(user_id)
        root_folder_id = session.query(Folder).filter(Folder.path == root_folder_path).first().id

        # Try to get the folder from the database
        datasource_folder = session.query(Folder).filter(Folder.path == fs_datasource_path).first()
        if not datasource_folder:
            # Create the folder in the database if it doesn't exist
            datasource_folder = Folder(
                name=datasource_create.name,
                path=fs_datasource_path,
                original_path=datasource_create.name,
                parent_id=root_folder_id
            )
            session.add(datasource_folder)
            session.flush()
        else:
            logger.info(f"Datasource folder already exists: {datasource_folder.path}")

        # Convert settings to a pydantic model to validate the data
        embedding_provider_class = get_embedding_provider_class(datasource_create.embedding_provider)
        embedding_settings = embedding_provider_class.model_validate_json(datasource_create.embedding_settings_json)
            
        # Create datasource
        datasource = Datasource(
            identifier=identifier,
            name=datasource_create.name,
            type=datasource_create.type,
            description=datasource_create.description,
            settings={}, #datasource_create.settings.model_dump_json(),
            embedding_provider=datasource_create.embedding_provider,
            embedding_settings=embedding_settings.model_dump_json(),
            root_folder_id=datasource_folder.id
        )
        session.add(datasource)
        session.commit()
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating datasource: {str(e)}")
        raise

async def delete_datasource(session: Session, user_id: str, identifier: str) -> None:
    """Delete a datasource and all its components"""
    # TODO Make more robust to avoid partial deletion by implementing a trash folder and moving the files to it and restoring them in case of an error
    try:
        datasource = session.query(Datasource).filter(Datasource.identifier == identifier).first()
        if not datasource:
            raise Exception("Datasource not found")

        # Store root folder reference before nullifying it
        root_folder = session.query(Folder).filter(Folder.id == datasource.root_folder_id).first()
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

    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting datasource: {str(e)}")
        logger.error(f"Failed to delete datasource files and folders: {str(e)}")
        # Restore the root_folder_id reference since deletion failed
        datasource.root_folder_id = root_folder.id
        session.commit()
        raise Exception(f"Failed to delete datasource files. Please try again later : {str(e)}")
        

def get_datasource(session: Session, identifier: str) -> DatasourceResponse:
    """Get a datasource by identifier"""
    try:
        datasource = session.query(Datasource).filter(Datasource.identifier == identifier).first()
        if not datasource:
            raise Exception("Datasource not found")
        return DatasourceResponse.from_model(datasource)
    except Exception as e:
        logger.error(f"Error getting datasource: {str(e)}")
        raise

def get_all_datasources(session: Session) -> List[DatasourceResponse]:
    """Get all datasources"""
    try:
        datasources = session.query(Datasource).all()
        return [DatasourceResponse.from_model(datasource) for datasource in datasources]
    except Exception as e:
        logger.error(f"Error getting all datasources: {str(e)}")
        raise

async def update_datasource(session: Session, user_id: str, identifier: str, datasource_update: DatasourceUpdate):
    """Update a datasource's description and its associated query tool"""
    try:
        datasource = session.query(Datasource).filter(Datasource.identifier == identifier).first()

        if not datasource:
            raise Exception("Datasource not found")
        # Match the embedding provider to the class
        embedding_provider_class = get_embedding_provider_class(datasource_update.embedding_provider)
        embedding_settings = embedding_provider_class.model_validate_json(datasource_update.embedding_settings_json)
        embedding_settings_json = embedding_settings.model_dump_json()
        # If the provider has changed, delete the llama index components
        if datasource.embedding_provider != datasource_update.embedding_provider or datasource.embedding_settings != embedding_settings_json:
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
            datasource.embedding_provider = datasource_update.embedding_provider
            datasource.embedding_settings = embedding_settings_json

        # Update description in database
        datasource.description = datasource_update.description
        session.commit()
    
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