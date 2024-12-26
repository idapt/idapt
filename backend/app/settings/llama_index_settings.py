import os
from llama_index.core.settings import Settings
from app.settings.model_initialization import init_llm, init_embedding_model
from app.settings.models import AppSettings


def update_llama_index_settings_from_app_settings(app_settings: AppSettings):
    """Update LlamaIndex settings with configured LLM and embedding models"""
    Settings.llm = init_llm(app_settings)
    Settings.embed_model = init_embedding_model(app_settings)
    
    # Set chunk settings
    Settings.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
    Settings.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "20"))