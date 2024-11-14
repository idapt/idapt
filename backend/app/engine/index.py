import logging
from typing import Optional

from llama_index.core.callbacks import CallbackManager
from llama_index.core.indices import VectorStoreIndex
from pydantic import BaseModel, Field
from llama_index.core import StorageContext
from app.engine.vectordb import get_vector_store
from app.engine.docdb import get_postgres_document_store

logger = logging.getLogger("uvicorn")


class IndexConfig(BaseModel):
    callback_manager: Optional[CallbackManager] = Field(
        default=None,
    )

global_index = None

def get_global_index():
    if global_index is None:
        global_index = create_index()
    return global_index


def create_index(config: IndexConfig = None):

    if config is None:
        config = IndexConfig()


    postgres_document_store = get_postgres_document_store()

    vector_store = get_vector_store()

    # Create storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store, docstore=postgres_document_store)

    # Load the index from the vector store
    # If you are using a vector store that doesn't store text,
    # you must load the index from both the vector store and the document store

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        callback_manager=config.callback_manager,
        storage_context=storage_context
    )


    logger.info("Finished loading index.")
    return index