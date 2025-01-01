#
#from llama_index.storage.docstore.postgres import PostgresDocumentStore
#from llama_index.vector_stores.postgres import PGVectorStore
#from llama_index.core.indices import VectorStoreIndex
#
#from urllib.parse import urlparse
#import asyncio
#
#from app.database.connection import get_connection_string
#from app.settings.manager import AppSettingsManager
#app_settings = AppSettingsManager.get_instance().settings
#
#import logging
#
#logger = logging.getLogger(__name__)
#
#class SingletonMeta(type):
#    _instances = {}
#
#    def __call__(cls, *args, **kwargs):
#        if cls not in cls._instances:
#            cls._instances[cls] = super().__call__(*args, **kwargs)
#        return cls._instances[cls]
#
#
#class ZettelkastenIndexSingleton(metaclass=SingletonMeta):
#
#    def __init__(self):
#        self._zettelkasten_index = None
#        self._doc_store = None
#        self._vector_store = None
#        self._loop = None
#        
#    @property
#    def zettelkasten_index(self):
#        if self._zettelkasten_index is None:
#          try:
#
#            vector_store = self.vector_store
#            doc_store = self.doc_store
#
#            self._zettelkasten_index = VectorStoreIndex.from_vector_store(
#                vector_store,
#                docstore=doc_store,
#            )
#            
#          except Exception as e:
#              logger.error(f"Error creating index: {e}")
#              raise e
#
#        return self._zettelkasten_index
#
#    @property
#    def doc_store(self):
#        if self._doc_store is None:
#            connection_string = get_connection_string()
#            self._doc_store = PostgresDocumentStore.from_uri(
#                connection_string,
#                schema_name="public",
#                table_name="zettelkasten_docstore"
#            )
#        return self._doc_store
#
#    @property
#    def vector_store(self):
#        current_loop = asyncio.get_event_loop()
#        
#        # If we're in a different loop, recreate the vector store
#        if self._loop is not None and self._loop != current_loop:
#            self._vector_store = None
#            
#        if self._vector_store is None:
#            self._loop = current_loop
#            
#            # Your existing initialization code
#            original_conn_string = get_connection_string()
#            original_scheme = urlparse(original_conn_string).scheme + "://"
#            conn_string = original_conn_string.replace(
#                original_scheme, "postgresql+psycopg2://"
#            )
#            async_conn_string = original_conn_string.replace(
#                original_scheme, "postgresql+asyncpg://"
#            )
#            
#            self._vector_store = PGVectorStore(
#                connection_string=conn_string,
#                async_connection_string=async_conn_string,
#                schema_name="public",
#                table_name="zettelkasten_vectorstore",
#                embed_dim=int(app_settings.embedding_dim),
#            )
#        return self._vector_store