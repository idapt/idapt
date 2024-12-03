# flake8: noqa: E402
from dotenv import load_dotenv
load_dotenv()
import logging
import os
from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from app.engine.loaders import get_documents, get_file_documents_from_paths
from app.engine.storage_context import StorageContextSingleton
from app.settings.llama_index_settings import update_llama_index_llm_and_embed_models_from_app_settings
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

SUPPORTED_EXTENSIONS = {'.txt', '.md'}

def run_pipeline(docstore, vector_store, documents):
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=Settings.chunk_size,
                chunk_overlap=Settings.chunk_overlap,
            ),
            Settings.embed_model,
        ],
        docstore=docstore,
        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,  # type: ignore
        vector_store=vector_store,
    )
    # Run the ingestion pipeline and store the results
    nodes = pipeline.run(show_progress=True, documents=documents)
    return nodes

def generate_files_embeddings(file_paths: List[str] = None):
    """Generate embeddings for specified files or all files if none specified"""
    
    update_llama_index_llm_and_embed_models_from_app_settings()

    logger.info(f"Generate embeddings for files: {file_paths if file_paths else 'all'}")
    
    if file_paths:
        # Get the documents for specified files or all files
        documents = get_file_documents_from_paths(file_paths)
    else:
        documents = get_documents()

    # Set private=false to mark the document as public (required for filtering)
    for doc in documents:
        doc.metadata["private"] = "false"

    # Run the ingestion pipeline
    _ = run_pipeline(
        StorageContextSingleton().doc_store,
        StorageContextSingleton().vector_store,
        documents
    )

    logger.info("Finished generating the index")