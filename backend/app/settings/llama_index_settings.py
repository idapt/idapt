import os
from typing import Dict

from llama_index.core.settings import Settings
from app.settings.model_initialization import init_llm, init_embedding_model


def update_llama_index_settings_from_app_settings():
    """Update LlamaIndex settings with configured LLM and embedding models"""
    Settings.llm = init_llm()
    Settings.embed_model = init_embedding_model()
    
    # Set chunk settings
    Settings.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
    Settings.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "20"))