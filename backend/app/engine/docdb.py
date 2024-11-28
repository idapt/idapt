from llama_index.storage.docstore.postgres import PostgresDocumentStore
from app.database.connection import get_connection_string
import asyncio

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DocStoreSingleton(metaclass=SingletonMeta):
    def __init__(self):
        self._doc_store = None
        self._loop = None

    @property
    def doc_store(self):
        current_loop = asyncio.get_event_loop()
        
        if self._loop is not None and self._loop != current_loop:
            self._doc_store = None
            
        if self._doc_store is None:
            self._loop = current_loop
            connection_string = get_connection_string()
            self._doc_store = PostgresDocumentStore.from_uri(
                connection_string,
                schema_name="public",
                table_name="docstore"
            )
        return self._doc_store
