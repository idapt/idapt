import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Use DATA_DIR from config
from app.config import DATA_DIR

# Set default config directory
APP_CONFIG_DIR = Path(os.getenv("APP_CONFIG_DIR", f"{DATA_DIR}/.app-config"))
SETTINGS_FILE = APP_CONFIG_DIR / "app-settings.json"

@dataclass
class _AppSettings:
    """Application settings with JSON persistence."""
    
    model_provider: str = "integrated_ollama"
    # Used when model_provider is custom_ollama defaults to localhost
    custom_ollama_host: str = "http://localhost:11434"
    # Set to big by default to avoid timeouts
    ollama_request_timeout: float = 2000
    model: str = "llama3.1:8b"
    embedding_model: str = "bge-m3"
    embedding_dim: str = "1024"
    top_k: int = 6
    system_prompt: str = (
        "You are an helpful personal assistant. "
        "You have access to the user personal journaling notes via the personal_notes_query_engine tool. "
        "Use it to answer user questions."
    )
    # The system prompt for the AI model.
    #SYSTEM_PROMPT="You are a DuckDuckGo search agent. 
    #You can use the duckduckgo search tool to get information from the web to answer user questions.
    #For better results, you can specify the region parameter to get results from a specific region but it's optional.
    #You are a Wikipedia agent. You help users to get information from Wikipedia.
    #If user request for a report or a post, use document generator tool to create a file and reply with the link to the file.

    def __post_init__(self):
        """Load settings from file right after instance creation"""
        self._load_settings()

    def _load_settings(self):
        """Load settings from JSON file if it exists."""
        try:
            # If the settings file exists, load the settings from it
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    # For each key-value pair in the data, set the attribute of the instance
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                logger.info("Loaded application settings from %s", SETTINGS_FILE)

            else:
                # If the settings file does not exist, create it and save the default settings
                self._save_settings()
                logger.info("Created default application settings at %s", SETTINGS_FILE)
        except Exception as e:
            logger.error("Error loading settings: %s", str(e))

    def _save_settings(self):
        """Save current settings to JSON file."""
        try:
            # Create all parent directories
            APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump(asdict(self), f, indent=2)
            logger.info("Saved application settings to %s", SETTINGS_FILE)
        except Exception as e:
            logger.error("Error saving settings: %s", str(e))

    def update(self, **kwargs):
        """Update settings with new values and save to file."""

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning("Unknown setting: %s", key)

        self._save_settings()

        # Set the custom Ollama host in nginx proxy
        from app.proxy import NginxProxy
        NginxProxy.set_custom_ollama_host(self.custom_ollama_host)

        # Update llama index settings after changing model settings
        from app.settings.llama_index_settings import update_llama_index_llm_and_embed_models_from_app_settings
        update_llama_index_llm_and_embed_models_from_app_settings()

        # Pull Ollama models currently set in app settings if needed
        if self.model_provider == "integrated_ollama" or self.model_provider == "custom_ollama":
            from app.pull_ollama_models import pull_ollama_models
            import threading
            threading.Thread(target=pull_ollama_models, args=[[self.model, self.embedding_model]], daemon=True).start()

# Create the singleton instance - settings will be loaded from file during initialization
AppSettings = _AppSettings() 