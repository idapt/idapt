import logging
from typing import Optional

from llama_index.core.callbacks import CallbackManager
from llama_index.core.indices import VectorStoreIndex, load_index_from_storage
from pydantic import BaseModel, Field
from llama_index.core import StorageContext
from app.engine.vectordb import get_vector_store
from app.engine.docdb import get_postgres_document_store

logger = logging.getLogger("uvicorn")


class IndexConfig(BaseModel):
    callback_manager: Optional[CallbackManager] = Field(
        default=None,
    )

# Singleton index instance to avoid creating multiple instances
index: VectorStoreIndex = None

# TODO Make this better
def get_index(config: IndexConfig = None):

    global index
    
    if config is None:
        config = IndexConfig()
    logger.info("Connecting vector store...")

    vector_store = get_vector_store()
    postgres_document_store = get_postgres_document_store()

    # create storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store, docstore=postgres_document_store)

    # Load the index from the vector store
    # If you are using a vector store that doesn't store text,
    # you must load the index from both the vector store and the document store
    index = VectorStoreIndex.from_vector_store(
        vector_store, callback_manager=config.callback_manager
    )

    logger.info("Finished load index from vector store.")
    return index

def refresh_index():
    global index
    index = None  # Force reinitialization
    return get_index()