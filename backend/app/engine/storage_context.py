from llama_index.storage.docstore.postgres import PostgresDocumentStore
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.storage.index_store.postgres import PostgresIndexStore
from llama_index.core.indices import VectorStoreIndex
from llama_index.core import load_index_from_storage

from urllib.parse import urlparse
import os
import asyncio

from app.database.connection import get_connection_string
from app.settings.app_settings import AppSettings

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class StorageContextSingleton(metaclass=SingletonMeta):
    def __init__(self):
        self._storage_context = None
        self._doc_store = None
        self._vector_store = None
        self._index_store = None
        self._index = None
        self._loop = None


    @property
    def storage_context(self):

        # Get the current event loop
        current_loop = asyncio.get_event_loop()
        
        # If we're in a different loop, recreate the storage context and everything else
        if self._loop is not None and self._loop != current_loop:
            
            self._storage_context = None
            
        if self._storage_context is None:
            
            self._loop = current_loop
            
            #persist_dir = "./output/storage_context"
            # Create the persist directory
            #os.makedirs(persist_dir, exist_ok=True)

            # Reset the variables to force the recreation of everything
            self._doc_store = None
            self._vector_store = None
            self._index_store = None
            self._index = None

            # Create the storage context
            self._storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store,
                docstore=self.doc_store,
                index_store=self.index_store,
                #persist_dir=persist_dir # Needed to init the storage context but it will not be used for remote stores
            )

        return self._storage_context

    @property
    def doc_store(self):
        if self._doc_store is None:
            connection_string = get_connection_string()
            self._doc_store = PostgresDocumentStore.from_uri(
                uri=connection_string,
                schema_name="public",
                table_name="docstore"
            )
        return self._doc_store

    @property
    def vector_store(self):        
        if self._vector_store is None:            
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

    @property
    def index_store(self):
        if self._index_store is None:
            self._index_store = PostgresIndexStore.from_uri(
                uri=get_connection_string(),
                schema_name="public",
                table_name="index"
            )
        return self._index_store
    
    @property
    def index(self):
        # TODO add loop management in stores also ?
        if self._index is None:
            try:
                # Load the index from the storage context
                self._index = load_index_from_storage(self.storage_context)
            except:
                # There are no nodes in the index store so we create an index from the vector store
                self._index = VectorStoreIndex(
                    nodes=[],
                    vector_store=self.vector_store,
                    docstore=self.doc_store,
                    storage_context=self.storage_context
                )
        return self._index