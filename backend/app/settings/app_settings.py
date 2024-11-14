import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

APP_CONFIG_DIR = Path(os.getenv("APP_CONFIG_DIR"))
SETTINGS_FILE = APP_CONFIG_DIR / "app-settings.json"

@dataclass
class _AppSettings:
    """Application settings with JSON persistence."""
    
    model_provider: str = "ollama"
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

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        """Load settings from JSON file if it exists."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                logger.info("Loaded application settings from %s", SETTINGS_FILE)
            else:
                self._save_settings()
                logger.info("Created default application settings at %s", SETTINGS_FILE)
        except Exception as e:
            logger.error("Error loading settings: %s", str(e))

    def _save_settings(self):
        """Save current settings to JSON file."""
        try:
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

# Singleton instance
AppSettings = _AppSettings() 