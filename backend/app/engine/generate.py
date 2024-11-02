from dotenv import load_dotenv
load_dotenv()

import logging
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Optional

from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.core.storage import StorageContext
from llama_index.core import Document

from app.engine.loaders import get_documents
from app.engine.vectordb import get_vector_store
from app.settings import init_settings
from app.database.models import Base, File, Folder, DataEmbeddings
from app.database.connection import get_connection_string
from app.config import DATA_DIR
from app.engine.node_processor import process_document_to_nodes, delete_nodes_for_file
from app.engine.storage.folders import get_or_create_folder
from app.engine.storage.files import read_file_content, create_file, delete_file
from app.engine.ingestion.processor import create_document, process_nodes_to_documents
from app.engine.ingestion.pipeline import create_ingestion_pipeline, process_documents

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.txt', '.md'}

def generate_datasource():
    """Main function to generate the datasource"""
    init_settings()
    logger.info("Generate index for the provided data")

    engine = create_engine(get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Initialize stores
        vector_store = get_vector_store()
        pipeline = create_ingestion_pipeline(vector_store)
        
        process_data(session, vector_store, pipeline)
        
        session.commit()
        logger.info("Successfully processed files and folders")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error during generation: {e}")
        raise
    finally:
        session.close()

def process_data(session, vector_store, pipeline):
    """Process all data files and folders"""
    existing_files = {(file.name, file.folder_id): (file.content, file.id) 
                     for file in session.query(File).all()}
    
    current_files = {}
    folder_cache = {}
    new_or_modified_docs = []
    
    # Process current files
    for root, dirs, files in os.walk(Path(DATA_DIR)):
        current_path = Path(root).relative_to(DATA_DIR)
        
        folder = None if str(current_path) == '.' else get_or_create_folder(session, current_path, folder_cache)
        
        process_directory_files(session, root, files, folder, current_files, existing_files, new_or_modified_docs)
    
    # Handle deleted files
    handle_deleted_files(session, existing_files, current_files)
    
    # Process documents
    if new_or_modified_docs:
        process_modified_documents(new_or_modified_docs, pipeline, vector_store)

def process_directory_files(
    session,
    root: str,
    files: list,
    folder,
    current_files: dict,
    existing_files: dict,
    new_or_modified_docs: list
):
    """Process files in a directory"""
    for file_name in files:
        if not any(file_name.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            continue

        file_path = Path(root) / file_name
        content = read_file_content(file_path)
        if content is None:
            continue

        folder_id = folder.id if folder else None
        current_files[(file_name, folder_id)] = content

        # Check if file exists and content has changed
        if (file_name, folder_id) in existing_files:
            existing_content, file_id = existing_files[(file_name, folder_id)]
            if content != existing_content:
                # Update existing file
                file = create_file(session, file_name, content, folder_id)
                doc = create_document(file, content)
                new_or_modified_docs.append(doc)
        else:
            # Create new file
            file = create_file(session, file_name, content, folder_id)
            doc = create_document(file, content)
            new_or_modified_docs.append(doc)

def handle_deleted_files(session, existing_files: dict, current_files: dict):
    """Handle files that have been deleted from the filesystem"""
    for (file_name, folder_id), (content, file_id) in existing_files.items():
        if (file_name, folder_id) not in current_files:
            delete_file(session, file_id)

def process_modified_documents(documents: list, pipeline, vector_store):
    """Process modified documents through the ingestion pipeline"""
    if not documents:
        return []
        
    logger.info(f"Processing {len(documents)} documents")
    all_nodes = []
    
    for doc in documents:
        file_id = doc.metadata.get("file_id")
        if file_id is None:
            logger.error(f"Document missing file_id in metadata: {doc.metadata}")
            continue
            
        # If file_id is already an int, use it directly
        if isinstance(file_id, int):
            file_id = file_id
        else:
            try:
                file_id = int(file_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid file_id in metadata: {file_id}")
                continue
                
        nodes = process_document_to_nodes(vector_store.session, doc, file_id)
        if nodes:
            all_nodes.extend(nodes)
            vector_store.session.commit()
            
    return all_nodes

if __name__ == "__main__":
    generate_datasource()
