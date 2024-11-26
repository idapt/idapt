import logging
from typing import Optional

from llama_index.core.callbacks import CallbackManager
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.storage import StorageContext
from app.engine.vectordb import VectorStoreSingleton
from app.engine.docdb import DocStoreSingleton

logger = logging.getLogger(__name__)

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class IndexSingleton(metaclass=SingletonMeta):

    def __init__(self):
        self._global_index = None
        self.callback_manager = None

    @property
    def global_index(self):
        if self._global_index is None:
            self._global_index = self.create_index(self.callback_manager)
            logger.info("Created index.")
        return self._global_index

    def get_global_index(self):
        return self.global_index

    def create_index(self, callback_manager: Optional[CallbackManager] = None):
        try:
            document_store = DocStoreSingleton().doc_store

            vector_store = VectorStoreSingleton().vector_store

            index = VectorStoreIndex.from_vector_store(
                vector_store,
                docstore=document_store,
                callback_manager=callback_manager,
            )
            
            return index
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise e

