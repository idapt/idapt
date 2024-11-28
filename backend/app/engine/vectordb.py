import os
from llama_index.vector_stores.postgres import PGVectorStore
from urllib.parse import urlparse
from app.database.connection import get_connection_string
from app.settings.app_settings import AppSettings
import asyncio


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class VectorStoreSingleton(metaclass=SingletonMeta):
    def __init__(self):
        self._vector_store = None
        self._loop = None

    @property
    def vector_store(self):
        current_loop = asyncio.get_event_loop()
        
        # If we're in a different loop, recreate the vector store
        if self._loop is not None and self._loop != current_loop:
            self._vector_store = None
            
        if self._vector_store is None:
            self._loop = current_loop
            
            # Your existing initialization code
            original_conn_string = get_connection_string()
            original_scheme = urlparse(original_conn_string).scheme + "://"
            conn_string = original_conn_string.replace(
                original_scheme, "postgresql+psycopg2://"
            )
            async_conn_string = original_conn_string.replace(
                original_scheme, "postgresql+asyncpg://"
            )
            
            self._vector_store = PGVectorStore(
                connection_string=conn_string,
                async_connection_string=async_conn_string,
                schema_name="public",
                table_name="embeddings",
                embed_dim=int(AppSettings.embedding_dim),
            )
        return self._vector_store