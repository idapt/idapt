import json
import logging
from pathlib import Path
import os

from app.settings.models import AppSettings
from app.services.user_path import get_user_app_data_dir

logger = logging.getLogger("uvicorn")

def get_app_settings(user_id: str) -> AppSettings:
    try:
        # Create the directory if it doesn't exist
        user_app_data_dir = get_user_app_data_dir(user_id)
        os.makedirs(user_app_data_dir, exist_ok=True)
        
        settings_file = Path(user_app_data_dir) / "app-settings.json"
        # If the settings file exists, load the settings from it and return it
        if settings_file.exists():
            data = json.loads(settings_file.read_text())
            settings = AppSettings.model_validate(data)
            #logger.info(f"Loaded settings from {settings_file}")
            return settings
        # If the settings file does not exist, create a default settings, save it and return it
        else:
            settings = AppSettings()
            settings_file.write_text(settings.model_dump_json(indent=2))
            logger.info(f"Created default settings at {settings_file}")
            return settings
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        raise e

def save_app_settings(user_id: str, settings: AppSettings) -> None:
    try:
        # Create the directory if it doesn't exist
        user_app_data_dir = get_user_app_data_dir(user_id)
        os.makedirs(user_app_data_dir, exist_ok=True)
        
        # Normalize the ollama URL
        settings.ollama.llm_host = normalize_url(settings.ollama.llm_host)
        settings.ollama.embedding_host = normalize_url(settings.ollama.embedding_host)
        
        settings_file = Path(user_app_data_dir) / "app-settings.json"
        settings_file.write_text(settings.model_dump_json(indent=2))
        logger.info(f"Saved settings to {settings_file}")
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        raise e
    
# Normalize an url
def normalize_url(url: str) -> str:
    """Normalize the URL to prevent double slashes and ensure proper formatting"""
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Ensure the URL has a scheme, default to http if none provided
    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"
        
    return url