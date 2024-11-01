import os
from llama_index.vector_stores.postgres import PGVectorStore
from urllib.parse import urlparse
from app.database.connection import get_connection_string

PGVECTOR_SCHEMA = "public"
PGVECTOR_TABLE = "embeddings"

vector_store: PGVectorStore = None


def get_vector_store():
    global vector_store

    if vector_store is None:

        original_conn_string = get_connection_string()

        original_scheme = urlparse(original_conn_string).scheme + "://"
        conn_string = original_conn_string.replace(
            original_scheme, "postgresql+psycopg2://"
        )
        async_conn_string = original_conn_string.replace(
            original_scheme, "postgresql+asyncpg://"
        )

        vector_store = PGVectorStore(
            connection_string=conn_string,
            async_connection_string=async_conn_string,
            schema_name=PGVECTOR_SCHEMA,
            table_name=PGVECTOR_TABLE,
            embed_dim=int(os.environ.get("EMBEDDING_DIM", 1024)),
        )

    return vector_store
