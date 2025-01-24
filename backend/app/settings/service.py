from sqlalchemy.orm import Session
from app.settings.models import Setting
from app.settings.schemas import *
from typing import Type, Dict, Any
import json
import logging

logger = logging.getLogger("uvicorn")

SETTING_MODELS: Dict[str, Type[SettingBase]] = {
    "app": AppSettings,
    "ollama_llm": OllamaLLMSettings,
    "openai_llm": OpenAILLMSettings,
    "anthropic_llm": AnthropicLLMSettings,
    "groq_llm": GroqLLMSettings,
    "gemini_llm": GeminiLLMSettings,
    "mistral_llm": MistralLLMSettings,
    "azure-openai_llm": AzureOpenAILLMSettings,
    "tgi_llm": TGILLMSettings,
}

def get_setting(session: Session, identifier: str) -> SettingBase:
    try:
        setting = session.query(Setting).filter(Setting.identifier == identifier).first()
        
        # Get the corresponding model class for this identifier
        model_class = SETTING_MODELS.get(identifier)
        if not model_class:
            raise ValueError(f"Unknown setting identifier: {identifier}")
            
        setting_value = None

        if not setting:
            # Create default setting if it doesn't exist
            setting_value = model_class()
            # Add it to the database
            db_setting = Setting(
                identifier=setting_value.identifier,
                display_name=setting_value.display_name,
                description=setting_value.description,
                # Dump the whole setting to json in the value field
                value=json.dumps(setting_value.model_dump())
            )
            session.add(db_setting)
            session.commit()
            session.refresh(db_setting)
            return model_class(**db_setting.__dict__)
        else:
            # The setting exists in the database, load it from the json field into the model class and return it
            setting_value = model_class(**json.loads(setting.value))
            return setting_value
    except Exception as e:
        logger.error(f"Error getting setting {identifier}: {str(e)}")
        raise ValueError(f"Error getting setting {identifier}: {str(e)}")

def update_setting(session: Session, identifier: str, json_setting_object_str: str) -> SettingBase:
    try:
        setting = session.query(Setting).filter(Setting.identifier == identifier).first()
        if not setting:
            raise ValueError(f"Setting not found: {identifier}")
        # Get the model class for the setting
        model_class = SETTING_MODELS.get(identifier)
        if not model_class:
            raise ValueError(f"Unknown setting identifier: {identifier}")
        # try to load the value from the json provided, this will do pydantic validation
        new_setting_value = None
        try:
            new_setting_value = model_class(**json_setting_object_str)
        except Exception as e:
            raise ValueError(f"Invalid value for setting {identifier}: {e}")
        # Update the setting JSON value in the database
        setting.value = json.dumps(new_setting_value.model_dump())
        session.commit()
        session.refresh(setting)
        return new_setting_value
    except Exception as e:
        logger.error(f"Error updating setting {identifier}: {str(e)}")
        raise ValueError(f"Error updating setting {identifier}: {str(e)}")