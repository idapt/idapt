import json
import logging
from pathlib import Path
from typing import Optional

from app.config import APP_DATA_DIR
from app.settings.models import AppSettings

logger = logging.getLogger(__name__)

class AppSettingsManager:
    _instance: Optional["AppSettingsManager"] = None
    _settings: Optional[AppSettings] = None
    
    def __init__(self):
        self.settings_file = Path(APP_DATA_DIR) / "app-settings.json"
        self._load_settings()
    
    @classmethod
    def get_instance(cls) -> "AppSettingsManager":
        if cls._instance is None:
            # Create a new instance
            cls._instance = cls()
            # Update the dependent services with the new settings
            cls._instance._update_dependent_services()
        return cls._instance
    
    @property
    def settings(self) -> AppSettings:
        if self._settings is None:
            self._load_settings()
        return self._settings
    
    def _load_settings(self) -> None:
        try:
            if self.settings_file.exists():
                data = json.loads(self.settings_file.read_text())
                self._settings = AppSettings.model_validate(data)
                logger.info(f"Loaded settings from {self.settings_file}")
            else:
                self._settings = AppSettings()
                self._save_settings()
                logger.info(f"Created default settings at {self.settings_file}")
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            self._settings = AppSettings()
    
    def _save_settings(self) -> None:
        try:
            self.settings_file.write_text(self.settings.model_dump_json(indent=2))
            logger.info(f"Saved settings to {self.settings_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
    
    def update(self, **kwargs) -> None:
        updated_data = self.settings.model_dump()
        updated_data.update(kwargs)
        self._settings = AppSettings.model_validate(updated_data)
        self._save_settings()
        
        # Update dependent services
        self._update_dependent_services()
    
    def _update_dependent_services(self) -> None:
        # Update llama index settings
        from app.settings.llama_index_settings import update_llama_index_settings_from_app_settings
        update_llama_index_settings_from_app_settings(self.settings)