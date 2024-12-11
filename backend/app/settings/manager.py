import json
import logging
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.settings.models import AppSettings

logger = logging.getLogger(__name__)

class SettingsManager:
    _instance: Optional["SettingsManager"] = None
    _settings: Optional[AppSettings] = None
    
    def __init__(self):
        self.config_dir = Path(DATA_DIR) / ".app-config"
        self.settings_file = self.config_dir / "app-settings.json"
        self._load_settings()
    
    @classmethod
    def get_instance(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = cls()
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
            self.config_dir.mkdir(parents=True, exist_ok=True)
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
        # Update nginx proxy
        #from app.proxy import NginxProxy
        #NginxProxy.set_custom_ollama_llm_host(str(self.settings.custom_ollama.llm_host))
        
        # Update llama index settings
        from app.settings.llama_index_settings import update_llama_index_settings_from_app_settings
        update_llama_index_settings_from_app_settings()
        
        # Pull Ollama models if needed
        if self.settings.llm_model_provider in ["integrated_ollama", "custom_ollama"]:
            from app.pull_ollama_models import start_ollama_pull_thread
            start_ollama_pull_thread() 