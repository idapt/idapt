from dotenv import load_dotenv
load_dotenv()

import logging
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Optional
from llama_index.core import Document

from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.core.storage import StorageContext

from app.engine.loaders import get_documents
from app.engine.document_db import get_doc_store
from app.engine.vectordb import get_vector_store
from app.settings import init_settings
from app.database.models import Base, File, Folder
from app.database.connection import get_connection_string
from app.config import DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
SUPPORTED_EXTENSIONS = {'.txt', '.md'}

def create_folder(session, name: str, parent_id: Optional[int] = None) -> Folder:
    """Create a new folder in the database"""
    folder = Folder(name=name, parent_id=parent_id)
    session.add(folder)
    session.flush()  # Flush to get the ID
    return folder

def get_or_create_folder(session, folder_path: Path, folder_cache: Dict[str, Folder]) -> Folder:
    """Get or create a folder and its parent folders"""
    if str(folder_path) in folder_cache:
        return folder_cache[str(folder_path)]

    if str(folder_path.parent) == '.':
        # Root folder
        folder = create_folder(session, folder_path.name)
    else:
        # Get or create parent folder first
        parent = get_or_create_folder(session, folder_path.parent, folder_cache)
        folder = create_folder(session, folder_path.name, parent.id)

    folder_cache[str(folder_path)] = folder
    return folder

def process_files_and_folders(session):
    """Process all files and folders in the data directory"""
    folder_cache: Dict[str, Folder] = {}
    data_path = Path(DATA_DIR)

    # Walk through all directories and files
    for root, dirs, files in os.walk(data_path):
        current_path = Path(root).relative_to(data_path)
        
        # Skip the root directory itself
        if str(current_path) != '.':
            folder = get_or_create_folder(session, current_path, folder_cache)
        else:
            folder = None

        # Process files in current directory
        for file in files:
            file_path = Path(file)
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                full_path = Path(root) / file
                
                # Read file content
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"Error reading file {full_path}: {e}")
                    continue

                # Create file record
                db_file = File(
                    name=file,
                    content=content,
                    folder_id=folder.id if folder else None
                )
                session.add(db_file)

def run_pipeline(docstore, vector_store, documents, doc_ids_to_delete=None):
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=Settings.chunk_size,
                chunk_overlap=Settings.chunk_overlap,
            ),
            Settings.embed_model,
        ],
        docstore=docstore,
        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
        vector_store=vector_store,
    )

    # Delete documents that no longer exist
    if doc_ids_to_delete:
        logger.info(f"Deleting {len(doc_ids_to_delete)} documents from stores")
        docstore.delete_documents(doc_ids_to_delete)
        vector_store.delete(doc_ids_to_delete)

    if documents:
        logger.info(f"Processing {len(documents)} documents")
        nodes = pipeline.run(show_progress=True, documents=documents)
        return nodes
    return []

def generate_datasource():
    init_settings()
    logger.info("Generate index for the provided data")

    # Initialize database connection
    engine = create_engine(get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get existing files from database
        existing_files = {(file.name, file.folder_id): (file.content, file.id) 
                        for file in session.query(File).all()}
        
        # Process current files and folders
        logger.info("Processing files and folders")
        current_files = {}
        folder_cache: Dict[str, Folder] = {}
        data_path = Path(DATA_DIR)
        
        # Track which documents need processing
        new_or_modified_docs = []
        doc_ids_to_delete = set()
        
        # Get the stores
        docstore = get_doc_store()
        vector_store = get_vector_store()

        # Walk through all directories and files
        for root, dirs, files in os.walk(data_path):
            current_path = Path(root).relative_to(data_path)
            
            folder = None
            if str(current_path) != '.':
                folder = get_or_create_folder(session, current_path, folder_cache)

            # Process files in current directory
            for file in files:
                file_path = Path(file)
                if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    full_path = Path(root) / file
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        logger.error(f"Error reading file {full_path}: {e}")
                        continue

                    folder_id = folder.id if folder else None
                    current_files[(file, folder_id)] = content

                    # Check if file is new or modified
                    if (file, folder_id) not in existing_files or existing_files[(file, folder_id)][0] != content:
                        db_file = File(
                            name=file,
                            content=content,
                            folder_id=folder_id
                        )
                        session.merge(db_file)
                        # Create document for new/modified file
                        doc = Document(text=content, metadata={
                            "file_name": file,
                            "private": "false",
                            "folder_id": str(folder_id) if folder_id else None
                        })
                        new_or_modified_docs.append(doc)

        # Find deleted files and their document IDs
        deleted_files = set(existing_files.keys()) - set(current_files.keys())
        if deleted_files:
            for file_name, folder_id in deleted_files:
                # Delete from database
                session.query(File).filter_by(name=file_name, folder_id=folder_id).delete()
                # Get document ID for deletion from vector store
                file_id = existing_files[(file_name, folder_id)][1]
                doc_ids = docstore.get_document_ids({"file_id": str(file_id)})
                doc_ids_to_delete.update(doc_ids)

        session.commit()
        logger.info("Successfully processed files and folders")

        # Run the ingestion pipeline only for new/modified documents
        if new_or_modified_docs or doc_ids_to_delete:
            _ = run_pipeline(docstore, vector_store, new_or_modified_docs, doc_ids_to_delete)

        logger.info("Finished generating the index")
    except Exception as e:
        session.rollback()
        logger.error(f"Error during generation: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    generate_datasource()
