from sqlalchemy.orm import Session
from typing import List
import json
import logging
from pathlib import Path

from app.datasources.file_manager.models import Folder
from app.datasources.file_manager.service.service import delete_folder
from app.datasources.file_manager.service.file_system import get_new_fs_path
from app.datasources.file_manager.service.llama_index import delete_datasource_llama_index_components, delete_files_in_folder_recursive_from_llama_index
from app.datasources.schemas import DatasourceResponse, DatasourceUpdate, DatasourceCreate
from app.datasources.utils import validate_name
from app.datasources.models import Datasource, DatasourceType
from app.settings.schemas import SettingResponse
from app.settings.service import get_all_settings, get_setting

logger = logging.getLogger("uvicorn")

def init_default_datasources_if_needed(session: Session, settings_db_session: Session):
    """Initialize default datasources if they don't exist"""
    try:
        # If there is no existing datasource create one, otherwise dont as the user explicitly deleted it, it will be recreated only if there are no other datasources
        if session.query(Datasource).count() != 0:
            return
        # Get the last embedding setting created from the database that ends with "_embed"
        all_settings : List[SettingResponse] = get_all_settings(settings_db_session)
        # Get the last embedding setting
        last_embedding_setting : SettingResponse = next((setting for setting in all_settings if setting.identifier.endswith("_embed")), None)
        # If there is no embedding setting, raise an error
        if not last_embedding_setting:
            raise Exception("No embedding setting found, create one first")

        # Create the default files datasource
        create_datasource(
            session=session,
            datasource_create=DatasourceCreate(
                name="Files",
                type=DatasourceType.FILES.name,
                description="Various files, prefer using another datasource if it seems more relevant",
                settings_json="{}",
                embedding_setting_identifier=last_embedding_setting.identifier
            )
        )

        # Create the chat history datasource
        create_datasource(
            session=session,
            datasource_create=DatasourceCreate(
                name="Chats",
                type=DatasourceType.CHATS.name,
                description="The chat history of the user with his AI assistant",
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
    settings_db_session: Session,
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
            # Get the last embedding setting created from the database that ends with "_embed"
            all_settings : List[SettingResponse] = get_all_settings(settings_db_session)
            # Get the last embedding setting
            embedding_setting : SettingResponse = next((setting for setting in all_settings if setting.identifier.endswith("_embed")), None)
            if not embedding_setting:
                raise ValueError(f"No embedding setting with schema_identifier ending with '_embed' found, create one first")
            embedding_setting_identifier = embedding_setting.identifier
        # If an embedding setting is provided
        else:
            # Check if the embedding setting identifier ends with "_embed"
            if not datasource_create.embedding_setting_identifier.endswith("_embed"):
                raise ValueError(f"Embedding setting with identifier '{datasource_create.embedding_setting_identifier}' is not of type '_embed'")
            # Check if the embedding setting exists
            embedding_setting : SettingResponse = get_setting(settings_db_session, datasource_create.embedding_setting_identifier)
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

async def update_datasource(session: Session, settings_db_session: Session, user_id: str, identifier: str, datasource_update: DatasourceUpdate):
    """Update a datasource's description and its associated query tool"""
    try:
        # Get the datasource to update
        datasource = session.query(Datasource).filter(Datasource.identifier == identifier).first()
        if not datasource:
            raise Exception("Datasource not found")
        # Try to get the embedding setting to see if it exists
        embedding_setting : SettingResponse = get_setting(settings_db_session, datasource_update.embedding_setting_identifier)
        if not embedding_setting:
            raise Exception(f"Embedding setting not found: {datasource_update.embedding_setting_identifier}")
        # If the provider has changed
        if datasource.embedding_setting_identifier != datasource_update.embedding_setting_identifier:
            # Get the old embedding setting
            old_embedding_setting : SettingResponse = get_setting(settings_db_session, datasource.embedding_setting_identifier)
            if not old_embedding_setting:
                raise Exception(f"Old embedding setting not found: {datasource.embedding_setting_identifier}")
            # Get the old embedding model
            old_embedding_model = json.loads(old_embedding_setting.value_json).get("model", "failed_model_get_string")
            # Get the new embedding model
            new_embedding_model = json.loads(embedding_setting.value_json).get("model", "failed_model_get_string")
            # If the embedding model has not changed, keep the processed llama index data
            if old_embedding_model == new_embedding_model and old_embedding_model != "failed_model_get_string" and new_embedding_model != "failed_model_get_string":
                logger.info(f"Embedding model has not changed, keeping processed llama index data: {old_embedding_model} == {new_embedding_model}")
            # If the embedding model has changed, delete the processed llama index data
            else:
                logger.info(f"Embedding model has changed, deleting processed llama index data: {old_embedding_model} != {new_embedding_model}")
                # Get root folder of datasource
                folder = session.query(Folder).filter(Folder.id == datasource.folder_id).first()
                if not folder:
                    raise Exception("Datasource has no root folder, try to delete and recreate it")
                # Delete the files in the folder from llama index
                delete_files_in_folder_recursive_from_llama_index(session, user_id, folder.path)
                # Delete the datasource llama index components
                delete_datasource_llama_index_components(datasource.identifier, user_id)
                logger.info(f"Deleted processed llama index data for datasource {datasource.identifier} and embedding model {old_embedding_model}")
            # New one will be created when first files are processed with it
            datasource.embedding_setting_identifier = datasource_update.embedding_setting_identifier

        if datasource_update.description:
            # Update description in database
            datasource.description = datasource_update.description

        session.commit()
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating datasource description: {str(e)}")
        raise