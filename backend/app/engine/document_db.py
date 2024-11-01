import os
from llama_index.storage.docstore.postgres import PostgresDocumentStore
from app.database.connection import get_connection_string

DOCSTORE_TABLE = "docstore"
DOCSTORE_SCHEMA = "public"

doc_store = None

def get_doc_store():
    """
    Get or create a PostgresDocumentStore instance.
    Uses the same database connection as the main application.
    """
    global doc_store

    if doc_store is None:
        connection_string = get_connection_string()
        
        # Create PostgresDocumentStore instance
        doc_store = PostgresDocumentStore.from_uri(
            uri=connection_string,
            namespace="default",
            table_name=DOCSTORE_TABLE,
            schema_name=DOCSTORE_SCHEMA,
            perform_setup=True,  # Create tables if they don't exist
            debug=False,
            use_jsonb=True  # Better performance for JSON operations
        )

    return doc_store
