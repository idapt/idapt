from llama_index.storage.docstore.postgres import PostgresDocumentStore
from app.database.connection import get_connection_string

# Singleton document store instance to avoid creating multiple instances
postgres_document_store: PostgresDocumentStore = None

def get_postgres_document_store() -> PostgresDocumentStore:
    """Get the Postgres document store"""
    # Return cached document store if it exists
    global postgres_document_store

    # Get the connection string
    connection_string = get_connection_string()
    
    # Build the PostgresDocumentStore
    postgres_document_store = PostgresDocumentStore.from_uri(connection_string)

    # Return the PostgresDocumentStore
    return postgres_document_store
