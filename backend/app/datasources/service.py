from pathlib import Path
from sqlalchemy.orm import Session
from typing import List

from app.api.user_path import get_user_data_dir
from app.file_manager.models import Folder
from app.file_manager.service.service import delete_folder
from app.file_manager.service.file_system import get_new_fs_path
from app.file_manager.service.llama_index import delete_datasource_llama_index_components, delete_files_in_folder_recursive_from_llama_index
from app.datasources.schemas import DatasourceResponse, DatasourceUpdate, DatasourceCreate
from app.datasources.utils import validate_name
from app.datasources.models import Datasource, DatasourceType
from app.settings.schemas import SETTING_CLASSES
from app.settings.models import Setting

import logging



logger = logging.getLogger("uvicorn")

def init_default_datasources_if_needed(session: Session):
    """Initialize default datasources if they don't exist"""
    try:
        # If there is no existing datasource create one, otherwise dont as the user explicitly deleted it, it will be recreated only if there are no other datasources
        if session.query(Datasource).count() != 0:
            return
        # Get the last embedding setting created from the database that ends with "_embed"
        last_embedding_setting = session.query(Setting).filter(Setting.identifier.endswith("_embed")).first()

        # Create the default files datasource
        create_datasource(
            session=session,
            datasource_create=DatasourceCreate(
                name="Files",
                type=DatasourceType.FILES,
                description="Various files, prefer using another datasource if it seems more relevant",
                settings_json="{}",
                embedding_setting_identifier=last_embedding_setting.identifier
            )
        )        
        logger.info("Default datasources initialized")

    except Exception as e:
        logger.error(f"Error initializing default datasources: {str(e)}")
        raise

def create_datasource(
    session: Session, 
    datasource_create: DatasourceCreate
) -> None:
    """Create a new datasource with its root folder and all required components"""
    try:
        # Check for invalid characters in name
        validate_name(datasource_create.name)
        
        # Check if datasource with this name already exists
        if session.query(Datasource).filter(Datasource.name == datasource_create.name).first():
            raise ValueError(f"Datasource with name '{datasource_create.name}' already exists")
        
        # If no embedding setting is provided, use the last one with the schema_identifier ending with "_embed"
        embedding_setting_identifier = None
        if not datasource_create.embedding_setting_identifier:
            embedding_setting = session.query(Setting).filter(Setting.schema_identifier.endswith("_embed")).first()
            if not embedding_setting:
                raise ValueError(f"No embedding setting with schema_identifier ending with '_embed' found, create one first")
            embedding_setting_identifier = embedding_setting.identifier
        # If an embedding setting is provided
        else:
            # Check if the embedding setting identifier ends with "_embed"
            if not datasource_create.embedding_setting_identifier.endswith("_embed"):
                raise ValueError(f"Embedding setting with identifier '{datasource_create.embedding_setting_identifier}' is not of type '_embed'")
            # Check if the embedding setting exists
            embedding_setting = session.query(Setting).filter(Setting.identifier == datasource_create.embedding_setting_identifier).first()
            if not embedding_setting:
                raise ValueError(f"Embedding setting with identifier '{datasource_create.embedding_setting_identifier}' does not exist")
            embedding_setting_identifier = datasource_create.embedding_setting_identifier

        # If the path already exists, the get_new_fs_path will append an uuid and get an unique path for it and create the required folders in the database
        fs_datasource_path = get_new_fs_path(original_path=datasource_create.name, session=session, last_path_part_is_file=False)
        # Get the created root folder for the datasource
        datasource_folder = session.query(Folder).filter(Folder.path == fs_datasource_path).first()
        # Extract the folder fs_name from its fs path last element and use it as datasource identifier
        datasource_identifier = fs_datasource_path.split("/")[-1]
        
        # Create datasource
        datasource = Datasource(
            # Extract the fs datasource folder name and use it as identifier
            identifier=datasource_identifier,
            name=datasource_create.name,
            type=datasource_create.type,
            description=datasource_create.description,
            settings_json=datasource_create.settings_json,
            embedding_setting_identifier=embedding_setting_identifier,
            folder_id=datasource_folder.id
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
        folder = session.query(Folder).filter(Folder.id == datasource.folder_id).first()
        if folder:
            # First remove the root_folder reference from datasource to allow deletion of all files and folders of this datasource
            datasource.root_folder_id = None
            session.flush()
            
            # Then try to delete all files and folders using the stored path
            await delete_folder(session, user_id, folder.path)
        else:
            logger.warning("Datasource has no root folder, still deleting it but this should not happen")

        # Delete the llama index components for this datasource
        delete_datasource_llama_index_components(datasource.identifier, user_id)

        # If file deletion succeeded, delete database entry
        session.delete(datasource)
        session.commit()

    except Exception as e:
        # Restore the folder_id reference since deletion failed
        session.rollback()
        logger.error(f"Error deleting datasource: {str(e)}")
        raise Exception(f"Failed to delete datasource files. Please try again later : {str(e)}")
        

def get_datasource(session: Session, identifier: str) -> DatasourceResponse:
    """Get a datasource by identifier"""
    try:
        datasource = session.query(Datasource).filter(Datasource.identifier == identifier).first()
        if not datasource:
            raise Exception("Datasource not found")
        return DatasourceResponse(
            identifier=datasource.identifier,
            name=datasource.name,
            type=datasource.type,
            description=datasource.description,
            settings_json=datasource.settings_json,
            embedding_setting_identifier=datasource.embedding_setting_identifier
        )
    except Exception as e:
        logger.error(f"Error getting datasource: {str(e)}")
        raise

def get_all_datasources(session: Session) -> List[DatasourceResponse]:
    """Get all datasources"""
    try:
        datasources = session.query(Datasource).all()
        return [
            DatasourceResponse(
            identifier=datasource.identifier,
            name=datasource.name,
            type=datasource.type,
            description=datasource.description,
            settings_json=datasource.settings_json,
            embedding_setting_identifier=datasource.embedding_setting_identifier
        )
        for datasource in datasources
        ]
    except Exception as e:
        logger.error(f"Error getting all datasources: {str(e)}")
        raise

async def update_datasource(session: Session, user_id: str, identifier: str, datasource_update: DatasourceUpdate):
    """Update a datasource's description and its associated query tool"""
    try:
        # Get the datasource to update
        datasource = session.query(Datasource).filter(Datasource.identifier == identifier).first()
        if not datasource:
            raise Exception("Datasource not found")
        # Try to get the embedding setting to see if it exists
        embedding_setting = session.query(Setting).filter(Setting.identifier == datasource_update.embedding_setting_identifier).first()
        if not embedding_setting:
            raise Exception(f"Embedding setting not found: {datasource_update.embedding_setting_identifier}")
        # If the provider has changed, delete the llama index components
        if datasource.embedding_setting_identifier != datasource_update.embedding_setting_identifier:
            # Get root folder of datasource
            folder = session.query(Folder).filter(Folder.id == datasource.folder_id).first()
            if not folder:
                raise Exception("Datasource has no root folder, try to delete and recreate it")
            # Delete the files in the folder from llama index
            delete_files_in_folder_recursive_from_llama_index(session, user_id, folder.path)
            # Delete the datasource llama index components
            delete_datasource_llama_index_components(datasource.identifier, user_id)
            # New one will be created when first files are processed with it
            datasource.embedding_setting_identifier = datasource_update.embedding_setting_identifier

        # Update description in database
        datasource.description = datasource_update.description
        session.commit()
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating datasource description: {str(e)}")
        raise