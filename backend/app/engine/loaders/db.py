import logging
import os
import yaml
from typing import List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DBLoaderConfig(BaseModel):
    uri: str
    queries: List[str]


def get_db_documents(configs: List[DBLoaderConfig] = None):
    if configs is None:
        # Load the YAML configuration
        with open('backend/config/loaders.yaml', 'r') as file:
            config = yaml.safe_load(file)

        # Substitute the environment variable for the DB URI
        db_uri = os.getenv('DB_URI', 'default_db_uri_if_not_set')
        configs = [
            DBLoaderConfig(uri=db_uri, queries=db_config.get('queries', []))
            for db_config in config.get('db', [])
        ]

    try:
        from llama_index.readers.database import DatabaseReader
    except ImportError:
        logger.error(
            "Failed to import DatabaseReader. Make sure llama_index is installed."
        )
        raise

    docs = []
    for entry in configs:
        loader = DatabaseReader(uri=entry.uri)
        for query in entry.queries:
            logger.info(f"Loading data from database with query: {query}")
            documents = loader.load_data(query=query)
            docs.extend(documents)

    return docs

# Example usage
if __name__ == "__main__":
    documents = get_db_documents()
    print(documents)
