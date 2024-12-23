from sqlalchemy.orm import Session
from app.database.models import Datasource, Folder
from app.services.database import DatabaseService
from app.services.db_file import DBFileService
from app.services.file_manager import FileManagerService
from app.services.file_system import get_full_path_from_path
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.storage.docstore.postgres import PostgresDocumentStore
from llama_index.storage.index_store.postgres import PostgresIndexStore
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.tools import BaseTool
from app.engine.tools.filtered_query_engine import FilteredQueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.retrievers import AutoMergingRetriever, VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.settings import Settings
from urllib.parse import urlparse
from app.database.connection import get_connection_string
from app.settings.manager import AppSettingsManager
import logging
from typing import List, Optional, Dict, Tuple
import re
from sqlalchemy import make_url


app_settings = AppSettingsManager.get_instance().settings

class DatasourceService:
    def __init__(self, database_service: DatabaseService, db_file_service: DBFileService, file_manager_service: FileManagerService):
        self.logger = logging.getLogger(__name__)
        self.database_service = database_service
        self.db_file_service = db_file_service
        self.file_manager_service = file_manager_service
        
        # Storage components
        self._vector_stores: Dict[str, PGVectorStore] = {}
        self._doc_stores: Dict[str, PostgresDocumentStore] = {}
        self._index_stores: Dict[str, PostgresIndexStore] = {}
        self._indices: Dict[str, VectorStoreIndex] = {}
        self._tools: Dict[str, BaseTool] = {}
        
        # Init the default datasource
        self._init_default_datasources(self.database_service.get_session())

    def _init_default_datasources(self, session: Session):
        """Initialize default datasources if they don't exist"""
        if not self.get_datasource(session, "Files"):
            self.create_datasource(
                session=session,
                name="Files",
                type="files",
                settings={"description": "Default file storage"}
            )

    def get_storage_components(self, datasource_name: str) -> Tuple[PGVectorStore, PostgresDocumentStore, PostgresIndexStore]:
        """Get or create all storage components for a datasource"""
        vector_store = self.get_vector_store(datasource_name)
        doc_store = self.get_doc_store(datasource_name)
        index_store = self.get_index_store(datasource_name)
        return vector_store, doc_store, index_store

    def get_vector_store(self, datasource_name: str) -> PGVectorStore:
        if datasource_name not in self._vector_stores:
            self._vector_stores[datasource_name] = self._create_vector_store(datasource_name)
        return self._vector_stores[datasource_name]

    def get_doc_store(self, datasource_name: str) -> PostgresDocumentStore:
        if datasource_name not in self._doc_stores:
            self._doc_stores[datasource_name] = self._create_doc_store(datasource_name)
        return self._doc_stores[datasource_name]

    def get_index_store(self, datasource_name: str) -> PostgresIndexStore:
        if datasource_name not in self._index_stores:
            self._index_stores[datasource_name] = self._create_index_store(datasource_name)
        return self._index_stores[datasource_name]

    def get_index(self, datasource_name: str) -> VectorStoreIndex:
        if datasource_name not in self._indices:
            self._indices[datasource_name] = self._create_index(datasource_name)
        return self._indices[datasource_name]

    def get_query_tool(self, datasource_name: str) -> BaseTool:
        if datasource_name not in self._tools:
            self._tools[datasource_name] = self._create_query_tool(datasource_name)
        return self._tools[datasource_name]

    def create_datasource(self, session: Session, name: str, type: str, settings: dict = None) -> Datasource:
        """Create a new datasource with its root folder and all required components"""
        try:
            path = name
            full_path = get_full_path_from_path(path)
            root_folder_id = self.db_file_service.get_folder_id(session, "/data")

            # Create root folder for datasource
            datasource_folder = Folder(
                name=name,
                path=full_path,
                parent_id=root_folder_id
            )
            session.add(datasource_folder)
            session.flush()

            # Create datasource
            datasource = Datasource(
                name=name,
                type=type,
                settings=settings,
                root_folder_id=datasource_folder.id
            )
            session.add(datasource)
            session.commit()

            # Initialize all llama-index components
            self.get_storage_components(name)
            self.get_index(name)
            self.get_query_tool(name)

            return datasource
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating datasource: {str(e)}")
            raise

    def delete_datasource(self, session: Session, name: str) -> bool:
        """Delete a datasource and all its components"""
        try:
            datasource = self.get_datasource(session, name)
            if datasource:
                # Delete filesystem and database entries
                self.file_manager_service.delete_folder(session, datasource.root_folder.path)
                session.delete(datasource)
                session.commit()

                # Delete llama-index components
                self._delete_llama_index_components(name)
                return True
            return False
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error deleting datasource: {str(e)}")
            raise

    def _delete_llama_index_components(self, datasource_name: str):
        """Delete all llama-index components for a datasource"""
        if datasource_name in self._vector_stores:
            self._vector_stores[datasource_name].delete_index()
            del self._vector_stores[datasource_name]
            
        if datasource_name in self._doc_stores:
            self._doc_stores[datasource_name].delete_index()
            del self._doc_stores[datasource_name]
            
        if datasource_name in self._index_stores:
            self._index_stores[datasource_name].delete_index()
            del self._index_stores[datasource_name]
            
        if datasource_name in self._indices:
            del self._indices[datasource_name]
            
        if datasource_name in self._tools:
            del self._tools[datasource_name]

    # Private methods for creating components
    def _create_vector_store(self, datasource_identifier: str) -> PGVectorStore:
        try:
            connection_string = get_connection_string()
            url = make_url(connection_string)
            vector_store = PGVectorStore.from_params(
                database=url.database,
                host=url.host,
                password=url.password,
                port=url.port,
                user=url.username,
                schema_name="public",
                table_name=f"embeddings_{datasource_identifier}",
                embed_dim=int(app_settings.embedding_dim),
                perform_setup=True,
                #hnsw_kwargs={
                #    "hnsw_m": 16,
                #    "hnsw_ef_construction": 64,
                #    "hnsw_ef_search": 40,
                #    "hnsw_dist_method": "vector_cosine_ops",
                #},
            )
            return vector_store
        except Exception as e:
            self.logger.error(f"Error creating vector store: {str(e)}")
            raise

    def _create_doc_store(self, datasource_name: str) -> PostgresDocumentStore:
        return PostgresDocumentStore.from_uri(
            uri=get_connection_string(),
            schema_name="public",
            table_name=f"docstore_{datasource_name.lower()}"
        )

    def _create_index_store(self, datasource_name: str) -> PostgresIndexStore:
        return PostgresIndexStore.from_uri(
            uri=get_connection_string(),
            schema_name="public",
            table_name=f"index_{datasource_name.lower()}"
        )

    def _create_index(self, datasource_name: str) -> VectorStoreIndex:
        vector_store, doc_store, index_store = self.get_storage_components(datasource_name)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            docstore=doc_store,
            index_store=index_store
        )
        return VectorStoreIndex(
            [],  # Empty nodes list for initial creation
            storage_context=storage_context
        )

    def _create_query_tool(self, datasource_name: str) -> BaseTool:
        index = self.get_index(datasource_name)
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=int(app_settings.top_k)
        )
        retriever = AutoMergingRetriever(
            retriever,
            storage_context=index.storage_context,
            verbose=True
        )
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",
            llm=Settings.llm
        )

        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )
        
        # Get datasource from database
        session = self.database_service.get_session()
        datasource = session.query(Datasource).filter(Datasource.name == datasource_name).first()
        # Create tool description
        description = ""
        if not datasource.description or datasource.description == "":
            description = f"Query engine for the {datasource_name} datasource"
        else:
            description = datasource.description

        # Add this instruction to the tool description for the agent to know how to use the tool # ? Great ?
        tool_description = f"{description}\nUse a detailed plain text question as input to the tool."
        
        return FilteredQueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name=f"{datasource_name.lower()}_query_engine",
                description=tool_description
            ),
        )

    def get_datasource(self, session: Session, name: str) -> Optional[Datasource]:
        """Get a datasource by name"""
        return session.query(Datasource).filter(Datasource.name == name).first()

    def get_all_datasources(self, session: Session) -> List[Datasource]:
        """Get all datasources"""
        return session.query(Datasource).all()
    
    def update_datasource_description(self, session: Session, name: str, description: str) -> bool:
        """Update a datasource's description and its associated query tool"""
        try:
            datasource = self.get_datasource(session, name)
            if datasource:
                # Update description in database
                datasource.description = description
                session.commit()

                # Update the query tool if it exists
                if name in self._tools:
                    # Create new tool description
                    tool_description = f"{description}\nUse a detailed plain text question as input to the tool."
                    
                    # Get existing query engine from current tool
                    existing_tool = self._tools[name]
                    if isinstance(existing_tool, FilteredQueryEngineTool):
                        query_engine = existing_tool._query_engine
                        
                        # Create new tool with updated description
                        self._tools[name] = FilteredQueryEngineTool(
                            query_engine=query_engine,
                            metadata=ToolMetadata(
                                name=f"{name.lower()}_query_engine",
                                description=tool_description
                            ),
                        )

                return True
            return False
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error updating datasource description: {str(e)}")
            raise
    
def get_datasource_name_from_path(path: str) -> str:
    """Get the datasource name from a path"""
    # Extract datasource name from path (first component after /data/)
    path_parts = path.split("/")
    data_index = path_parts.index("data")
    if data_index + 1 >= len(path_parts):
        raise ValueError(f"Invalid file path structure: {path}")
    return path_parts[data_index + 1]