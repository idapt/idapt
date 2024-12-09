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
    
    # Model names for each provider
    ollama_model: str = "llama3.1:8b"
    openai_model: str = "gpt-3.5-turbo"
    anthropic_model: str = "claude-3-sonnet"
    groq_model: str = "mixtral-8x7b-v0.1"
    gemini_model: str = "gemini-pro"
    mistral_model: str = "mistral-medium"
    azure_openai_model: str = "gpt-4"
    tgi_model: str = "llama3.1"

    # Used when model_provider is integrated_ollama and cant be changed
    integrated_ollama_llm_host: str = "http://idapt-nginx:3030/integrated-ollama"
    # Used when model_provider is custom_ollama defaults to localhost
    custom_ollama_llm_host: str = "http://idapt-nginx:3030/local-ollama" # Use this if you want to use the local ollama instance running on the localhost at port 11434
    # Used when model_provider is text-generation-inference
    tgi_host: str = ""

    # Set to big by default to avoid timeouts
    ollama_request_timeout: float = 2000
    tgi_request_timeout: float = 500
    
    # Embedding model settings
    embedding_model_provider: str = "integrated_ollama"
    ollama_embedding_model: str = "Losspost/stella_en_1.5b_v5"
    custom_ollama_embedding_model: str = "Losspost/stella_en_1.5b_v5"
    openai_embedding_model: str = "text-embedding-3-large"
    azure_openai_embedding_model: str = "text-embedding-ada-002"
    gemini_embedding_model: str = "embedding-001"
    mistral_embedding_model: str = "mistral-embed"
    fastembed_embedding_model: str = "all-MiniLM-L6-v2"
    tei_model: str = "nvidia/NV-Embed-v2"

    # Used when embedding_model_provider is integrated_ollama
    integrated_ollama_embedding_host: str = "http://idapt-nginx:3030/integrated-ollama"
    # Used when embedding_model_provider is custom_ollama
    custom_ollama_embedding_host: str = "http://idapt-nginx:3030/local-ollama"
    # Used when embedding_model_provider is text-embeddings-inference
    tei_host: str = ""

    embedding_dim: str = "1536"
    top_k: int = 15
    openai_api_key: str = ""
    system_prompt: str = (
        "You are an helpful personal assistant, be friendly with the user, talk to him like you are its helpful best friend. Act like you know him very well and like you know everything that you retrieve via the tools.\n"
        "You can use tools to answer user questions.\n"
        "You can access to the files of the user containing personal information about the user, you can use it to answer personal questions.\n"
        "When the user is talking at the first person, he is talking about himself. Use the tool to get personal information needed to answer.\n"
        "In your final answer strictly answer to the user question, do not go off topic or talk about tools used.\n"
    )
    max_iterations: int = 14
    files_tool_description: str = (
        "This tool provides information about the user files.\n"
        "Use a detailed plain text question as input to the tool."
    )

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
        NginxProxy.set_custom_ollama_llm_host(self.custom_ollama_llm_host)

        # Update llama index settings after changing model settings
        from app.settings.llama_index_settings import update_llama_index_settings_from_app_settings
        update_llama_index_settings_from_app_settings()

        # Pull Ollama models currently set in app settings if needed
        if self.model_provider == "integrated_ollama" or self.model_provider == "custom_ollama":
            from app.pull_ollama_models import start_ollama_pull_thread
            start_ollama_pull_thread()

# Create the singleton instance - settings will be loaded from file during initialization
AppSettings = _AppSettings() 