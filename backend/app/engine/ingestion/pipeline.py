import logging
from typing import List
from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings

logger = logging.getLogger(__name__)

def create_ingestion_pipeline(vector_store) -> IngestionPipeline:
    """Create an ingestion pipeline with default settings"""
    return IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=Settings.chunk_size,
                chunk_overlap=Settings.chunk_overlap,
            ),
            Settings.embed_model,
        ],
        vector_store=vector_store,
    )

def process_documents(pipeline: IngestionPipeline, documents: List[Document]) -> List:
    """Process documents through the ingestion pipeline"""
    if not documents:
        return []
        
    logger.info(f"Processing {len(documents)} documents")
    return pipeline.run(
        show_progress=True,
        documents=documents,
        return_nodes=True
    )