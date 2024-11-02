from typing import List
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from sqlalchemy.orm import Session

from app.database.models import Node, File

def process_document_to_nodes(
    session: Session,
    document: Document,
    file_id: int
) -> List[Node]:
    """Process a document into nodes and store them in the database"""
    # Initialize the sentence splitter
    splitter = SentenceSplitter(
        chunk_size=Settings.chunk_size,
        chunk_overlap=Settings.chunk_overlap,
    )
    
    # Split document into nodes
    nodes = splitter.get_nodes_from_documents([document])
    
    # Create Node records
    db_nodes = []
    for node in nodes:
        db_node = Node(
            node_id=node.node_id,
            text=node.text,
            metadata_=node.metadata,
            file_id=file_id
        )
        session.add(db_node)
        db_nodes.append(db_node)
    
    return db_nodes

def delete_nodes_for_file(session: Session, file_id: int) -> None:
    """Delete all nodes associated with a file"""
    session.query(Node).filter_by(file_id=file_id).delete()
