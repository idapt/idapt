from typing import List
from llama_index.core import Document
from sqlalchemy.orm import Session
from app.engine.node_processor import process_document_to_nodes
from app.database.models import File

def create_document(file: File, content: str) -> Document:
    """Create a Document object from file data"""
    return Document(text=content, metadata={
        "file_name": file.name,
        "private": "false",
        "folder_id": str(file.folder_id) if file.folder_id else None,
        "file_id": file.id
    })

def process_nodes_to_documents(session: Session, nodes: List, file: File) -> List[Document]:
    """Process nodes into embedding documents"""
    embedding_docs = []
    for node in nodes:
        embedding_doc = Document(
            text=node.text,
            metadata={
                "file_id": str(file.id),
                "node_id": node.node_id,
                "file_name": file.name,
                "private": "false",
                "folder_id": str(file.folder_id) if file.folder_id else None
            }
        )
        embedding_docs.append(embedding_doc)
    return embedding_docs