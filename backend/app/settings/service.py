from sqlalchemy.orm import Session
from app.settings.database.models import Setting
from app.settings.schemas import *
from typing import List
import json
import logging

logger = logging.getLogger("uvicorn")

def init_default_settings_if_needed(settings_db_session: Session):
    """Initialize default settings if they don't exist"""
    try:

        if not settings_db_session.query(Setting).filter(Setting.identifier == "default_ollama_embed").first():
            # Create the default ollama_embed setting
            create_setting(settings_db_session, "default_ollama_embed", CreateSettingRequest(
                schema_identifier="ollama_embed"
            ))
            logger.info("Default ollama_embed setting created")

        if not settings_db_session.query(Setting).filter(Setting.identifier == "default_ollama_llm").first():
            # Create the default ollama_llm setting
            create_setting(settings_db_session, "default_ollama_llm", CreateSettingRequest(
                schema_identifier="ollama_llm"
            ))
            logger.info("Default ollama_llm setting created")

        if not settings_db_session.query(Setting).filter(Setting.identifier == "app").first():
            # Create the default app setting
            create_setting(settings_db_session, "app", CreateSettingRequest(
                schema_identifier="app"
            ))
            logger.info("Default app setting created")

    except Exception as e:
        logger.error(f"Error initializing default settings: {str(e)}")
        raise

def create_setting(settings_db_session: Session, identifier: str, create_setting_request: CreateSettingRequest):
    try:
        # Get the model class for the setting
        model_class = SETTING_CLASSES.get(create_setting_request.schema_identifier)
        if not model_class:
            raise ValueError(f"Unknown setting schema identifier: {create_setting_request.schema_identifier}")
        # Check if the setting already exists
        if settings_db_session.query(Setting).filter(Setting.identifier == identifier).first():
            raise ValueError(f"Setting already exists: {identifier}")
        # Create a default setting from the model class
        default_setting_value = model_class()
        setting = Setting(
            identifier=identifier,
            schema_identifier=create_setting_request.schema_identifier,
            setting_schema_json=default_setting_value.model_json_schema(),
            value_json=default_setting_value.model_dump_json()
        )
        settings_db_session.add(setting)
        settings_db_session.commit()
    except Exception as e:
        settings_db_session.rollback()
        logger.error(f"Error creating setting: {str(e)}")
        raise

def get_all_settings(settings_db_session: Session) -> List[SettingResponse]:
    try:
        # Only return the identifiers ?
        settings = settings_db_session.query(Setting).all()
        return [
                SettingResponse(
                    identifier=setting.identifier,
                    schema_identifier=setting.schema_identifier,
                    setting_schema_json=json.dumps(setting.setting_schema_json),
                    value_json=setting.value_json
                ) for setting in settings
        ]
    except Exception as e:
        logger.error(f"Error getting all settings: {str(e)}")
        raise ValueError(f"Error getting all settings: {str(e)}")

def get_setting(settings_db_session: Session, identifier: str) -> SettingResponse:
    try:
        # Get the setting from the database
        setting = settings_db_session.query(Setting).filter(Setting.identifier == identifier).first()
        if not setting:
            raise ValueError(f"Setting not found: {identifier}")
        
        return SettingResponse(
            identifier=setting.identifier,
            schema_identifier=setting.schema_identifier,
            setting_schema_json=json.dumps(setting.setting_schema_json),
            value_json=setting.value_json
        )
    except Exception as e:
        logger.error(f"Error getting setting {identifier}: {str(e)}")
        raise ValueError(f"Error getting setting {identifier}: {str(e)}")
    
def get_all_settings_with_schema_identifier(settings_db_session: Session, schema_identifier: str) -> List[SettingResponse]:
    try:
        settings = settings_db_session.query(Setting).filter(Setting.schema_identifier == schema_identifier).all()
        if not settings:
            raise ValueError(f"Setting not found: {schema_identifier}")
        return [
            SettingResponse(
                identifier=setting.identifier,
                schema_identifier=setting.schema_identifier,
                setting_schema_json=json.dumps(setting.setting_schema_json),
                value_json=setting.value_json
            ) for setting in settings
        ]
    except Exception as e:
        logger.error(f"Error getting setting by schema identifier {schema_identifier}: {str(e)}")
        raise ValueError(f"Error getting setting by schema identifier {schema_identifier}: {str(e)}")

def update_setting(settings_db_session: Session, identifier: str, update_setting_request: UpdateSettingRequest):
    try:
        # Get the setting from the database
        db_setting = settings_db_session.query(Setting).filter(Setting.identifier == identifier).first()
        if not db_setting:
            raise ValueError(f"Setting not found: {identifier}")
        # Get the model class for the setting
        model_class = SETTING_CLASSES.get(db_setting.schema_identifier) # ? Use the schema in the setting ?
        if not model_class:
            raise ValueError(f"Can't find model class for setting schema: {db_setting.schema_identifier}")
        # Load the current value from the database into the model class
        current_setting_value = model_class.model_validate_json(db_setting.value_json)
        # Load the new value from the json into a dictionary
        new_setting_values = json.loads(update_setting_request.values_to_update_json)
        # Update the setting using the new value with the class method
        current_setting_value.update_value(new_setting_values)
        # Update the setting JSON value in the database
        db_setting.value_json = current_setting_value.model_dump_json()
        settings_db_session.commit()
        settings_db_session.refresh(db_setting)
    except Exception as e:
        settings_db_session.rollback()
        logger.error(f"Error updating setting {identifier}: {str(e)}")
        raise ValueError(f"Error updating setting {identifier}: {str(e)}")
    
def delete_setting(settings_db_session: Session, identifier: str):
    try:
        settings_db_session.query(Setting).filter(Setting.identifier == identifier).delete()
        settings_db_session.commit()
    except Exception as e:
        settings_db_session.rollback()
        logger.error(f"Error deleting setting {identifier}: {str(e)}")
        raise ValueError(f"Error deleting setting {identifier}: {str(e)}")