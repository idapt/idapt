from sqlalchemy.orm import Session
from app.database.models import Datasource, Folder
from app.services.database import get_session
from app.services.db_file import get_folder_id
from app.services.file_manager import delete_folder
from app.services.file_system import get_full_path_from_path
from app.settings.manager import AppSettingsManager

from llama_index.core.indices import VectorStoreIndex
from llama_index.core.tools import BaseTool, QueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.retrievers import VectorIndexRetriever#, AutoMergingRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.settings import Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
import chromadb

import logging
from typing import List, Optional, Dict, Tuple
import re
from sqlalchemy import text
from pathlib import Path

logger = logging.getLogger(__name__)


    # Storage components
    #self._vector_stores: Dict[str, ChromaVectorStore] = {}
    #self._doc_stores: Dict[str, SimpleDocumentStore] = {}
    #self._index_stores: Dict[str, SimpleIndexStore] = {}
    #self._indices: Dict[str, VectorStoreIndex] = {}
    #self._tools: Dict[str, BaseTool] = {}
    
    # Init the default datasource
    #with get_session() as session:
    #    _init_default_datasources(session)

def _init_default_datasources(session: Session):
    """Initialize default datasources if they don't exist"""
    try:
        if not get_datasource(session, "files"):
            create_datasource(
                session=session,
                name="Files",
                type="files",
                settings={}
            )
    except Exception as e:
        logger.error(f"Error initializing default datasources: {str(e)}")
        raise

def get_storage_components(session: Session, datasource_identifier: str) -> Tuple[ChromaVectorStore, SimpleDocumentStore, SimpleIndexStore]:
    """Get or create all storage components for a datasource"""
    try:
        vector_store = get_vector_store(session, datasource_identifier)
        doc_store = get_doc_store(session, datasource_identifier)
        index_store = get_index_store(session, datasource_identifier)
        return vector_store, doc_store, index_store
    except Exception as e:
        logger.error(f"Error getting storage components: {str(e)}")
        raise

def get_vector_store(session: Session, datasource_identifier: str) -> ChromaVectorStore:
    # TODO Add caching
    return _create_vector_store(session, datasource_identifier)

def get_doc_store(self, session: Session, datasource_identifier: str) -> SimpleDocumentStore:
    # TODO Add caching
    return _create_doc_store(session, datasource_identifier)

def get_index_store(self, session: Session, datasource_identifier: str) -> SimpleIndexStore:
    # TODO Add caching
    return _create_index_store(session, datasource_identifier)

def get_index(self, session: Session, datasource_identifier: str) -> VectorStoreIndex:
    # TODO Add caching
    return _create_index(session, datasource_identifier)

def get_query_tool(self, session: Session, datasource_identifier: str) -> BaseTool:
    # TODO Add caching
    return _create_query_tool(session, datasource_identifier)

def create_datasource(session: Session, name: str, type: str, settings: dict = None) -> Datasource:
    """Create a new datasource with its root folder and all required components"""
    try:
        identifier = generate_identifier(name)
        # Check if the identifier is already used
        if get_datasource(session, identifier):
            raise ValueError(f"Datasource with identifier '{identifier}' already exists")

        path = identifier
        full_path = get_full_path_from_path(path)
        root_folder_id = get_folder_id(session, "/data")

        # Create root folder for datasource
        datasource_folder = Folder(
            name=name,  # Use display name for folder
            path=full_path,
            parent_id=root_folder_id
        )
        session.add(datasource_folder)
        session.flush()

        # Create datasource
        datasource = Datasource(
            identifier=identifier,  # Add identifier
            name=name,
            type=type,
            settings=settings,
            root_folder_id=datasource_folder.id
        )
        session.add(datasource)
        session.commit()

        # Initialize all llama-index components using identifier
        get_storage_components(session, identifier)
        get_index(session, identifier)
        get_query_tool(session, identifier)

        return datasource
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating datasource: {str(e)}")
        raise

async def delete_datasource(session: Session, identifier: str) -> bool:
    """Delete a datasource and all its components"""
    try:
        datasource = get_datasource(session, identifier)
        if not datasource:
            return False

        # Store root folder reference before nullifying it
        root_folder = datasource.root_folder
        if not root_folder:
            raise Exception("Datasource has no root folder")
        
        root_folder_path = root_folder.path
        
        # First remove the root_folder reference from datasource
        datasource.root_folder_id = None
        session.flush()
        
        # Then try to delete all files and folders using the stored path
        try:
            await delete_folder(session, root_folder_path)
        except Exception as e:
            logger.error(f"Failed to delete datasource files and folders: {str(e)}")
            # Restore the root_folder_id reference since deletion failed
            datasource.root_folder_id = root_folder.id
            session.flush()
            raise Exception("Failed to delete datasource files. Please try again later.")

        # If file deletion succeeded, delete database entry
        session.delete(datasource)
        session.commit()

        # Delete llama-index components
        _delete_llama_index_components(identifier)
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting datasource: {str(e)}")
        raise

def _delete_llama_index_components(session: Session, datasource_identifier: str):
    """Delete all llama-index components for a datasource"""
    try:
        # Drop the tables if they exist
        with get_session() as session:
            # Drop vector store table
            query = text('DROP TABLE IF EXISTS public.data_{}_{}'.format(
                datasource_identifier, "embeddings"))
            session.execute(query)

            # Drop doc store table
            query = text('DROP TABLE IF EXISTS public.data_{}_{}'.format(
                datasource_identifier, "docstore"))
            session.execute(query)

            # Drop index store table
            query = text('DROP TABLE IF EXISTS public.data_{}_{}'.format(
                datasource_identifier, "index"))
            session.execute(query)
                            
            session.commit()
        
        # Clean up the in-memory references
        # TODO Add caching

    except Exception as e:
        logger.error(f"Error deleting llama-index components: {str(e)}")
        raise

# Private methods for creating components
def _create_vector_store(datasource_identifier: str) -> ChromaVectorStore:
    try:
        # Create the embeddings directory if it doesn't exist
        embeddings_dir = Path("/data/.idapt/embeddings")
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        embeddings_file = embeddings_dir / f"{datasource_identifier}"
        
        # Create a Chroma persistent client
        client = chromadb.PersistentClient(path=str(embeddings_file))
        # Create a Chroma collection
        chroma_collection = client.get_or_create_collection(name=datasource_identifier)
        # Create a Chroma vector store
        vector_store = ChromaVectorStore.from_collection(
            chroma_collection
        )
        return vector_store
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise

def _create_doc_store(datasource_identifier: str) -> SimpleDocumentStore:
    try:
        # Create the docstore directory if it doesn't exist
        docstores_dir = Path("/data/.idapt/docstores")
        docstores_dir.mkdir(parents=True, exist_ok=True)
        docstores_file = docstores_dir / f"{datasource_identifier}.json"

        docstore = None
        # If the file doesn't exist, create a new docstore and persist it
        if not docstores_file.exists():
            docstore = SimpleDocumentStore()
            docstore.persist(persist_path=str(docstores_file))
        else:
            docstore = SimpleDocumentStore.from_persist_path(
                str(docstores_file)
            )

        return docstore
    except Exception as e:
        logger.error(f"Error creating doc store: {str(e)}")
        raise

def _create_index_store(datasource_identifier: str) -> SimpleIndexStore:
    try:
        # Create the index store directory if it doesn't exist
        indexstores_dir = Path("/data/.idapt/indexstores") / datasource_identifier
        indexstores_dir.mkdir(parents=True, exist_ok=True)
        indexstores_file = indexstores_dir / f"{datasource_identifier}.json"
        
        index_store = None
        # If the file doesn't exist, create a new index store and persist it
        if not indexstores_file.exists():
            index_store = SimpleIndexStore()
            index_store.persist(persist_path=str(indexstores_file))
        else:
            index_store = SimpleIndexStore.from_persist_path(
                str(indexstores_file)
            )
        return index_store
    except Exception as e:
        logger.error(f"Error creating index store: {str(e)}")
        raise

def _create_index(datasource_identifier: str) -> VectorStoreIndex:
    try:
        vector_store, doc_store, _ = get_storage_components(datasource_identifier)
        # Recreate the index from the vector store and doc store at each app restart if needed
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            docstore=doc_store,
            #index_store=index_store # Remove index store support for now as it is not thought to be important
        )
        return index
        #storage_context = StorageContext.from_defaults(
        #    vector_store=vector_store,
        #    docstore=doc_store,
        #    index_store=index_store
        #)
        #return VectorStoreIndex(
        #    [],  # Empty nodes list for initial creation
        #    storage_context=storage_context
        #)
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def _create_query_tool(session: Session, datasource_identifier: str) -> BaseTool:
    try:
        index = get_index(datasource_identifier)

        app_settings = AppSettingsManager.get_instance().settings

        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=int(app_settings.top_k),
        )
        # Don't use this for now as we are not using hierarchical node parser
        #retriever = AutoMergingRetriever(
        #    retriever,
        #    storage_context=index.storage_context,
        #    verbose=True
        #)
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",
            llm=Settings.llm
        )

        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )
        
        # Get datasource info within session and extract needed data
        description = ""
        datasource = session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
        if not datasource or not datasource.description or datasource.description == "":
            description = f"Query engine for the {datasource_identifier} datasource"
        else:
            description = datasource.description

        # Add this instruction to the tool description for the agent to know how to use the tool # ? Great ?
        tool_description = f"{description}\nUse a detailed plain text question as input to the tool."
        
        return QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name=f"{datasource_identifier}_query_engine",
                description=tool_description
            ),
            resolve_input_errors=True
        )
    except Exception as e:
        logger.error(f"Error creating query tool: {str(e)}")
        raise

def get_datasource(session: Session, identifier: str) -> Optional[Datasource]:
    """Get a datasource by identifier"""
    return session.query(Datasource).filter(Datasource.identifier == identifier).first()

def get_all_datasources(session: Session) -> List[Datasource]:
    """Get all datasources"""
    return session.query(Datasource).all()

def update_datasource_description(session: Session, identifier: str, description: str) -> bool:
    """Update a datasource's description and its associated query tool"""
    try:
        datasource = get_datasource(session, identifier)
        if datasource:
            # Update description in database
            datasource.description = description
            session.commit()

            # Update the query tool description by recreating the tool
            # TODO Add caching

            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating datasource description: {str(e)}")
        raise
    
def get_datasource_identifier_from_path(path: str) -> str:
    """Get the datasource identifier from a path"""
    try:
        # Extract datasource name from path (first component after /data/)
        path_parts = path.split("/")
        data_index = path_parts.index("data")
        if data_index + 1 >= len(path_parts):
            raise ValueError(f"Invalid file path structure: {path}")
        return path_parts[data_index + 1]
    except Exception as e:
        # Do not use logger here
        raise ValueError(f"Invalid file path structure: {path}")

def generate_identifier(name: str) -> str:
    """Generate a safe identifier from a name"""
    try:
        # Convert to lowercase and replace spaces/special chars with underscores
        identifier = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        # Remove consecutive underscores
        identifier = re.sub(r'_+', '_', identifier)
        # Remove leading/trailing underscores
        identifier = identifier.strip('_')
        return identifier
    except Exception as e:
        # Do not use logger here
        raise ValueError(f"Invalid name: {name}")
