import logging
from typing import Any, Dict, List

import yaml  # type: ignore
from app.engine.loaders.db import DBLoaderConfig, get_db_documents
from app.engine.loaders.file import FileLoaderConfig, get_file_documents
from app.engine.loaders.web import WebLoaderConfig, get_web_documents
from llama_index.core import Document
from app.database.connection import get_connection_string

logger = logging.getLogger(__name__)


def load_configs() -> Dict[str, Any]:
    with open("config/loaders.yaml") as f:
        configs = yaml.safe_load(f)
    return configs

def get_file_documents_from_paths(file_paths: List[str]) -> List[Document]:
    config = load_configs()
    return get_file_documents(FileLoaderConfig(**config["file"]), file_paths)

def get_documents() -> List[Document]:
    documents = []
    config = load_configs()
    for loader_type, loader_config in config.items():
        logger.info(
            f"Loading documents from loader: {loader_type}, config: {loader_config}"
        )
        match loader_type:
            case "file":
                document = get_file_documents(FileLoaderConfig(**loader_config))
            case "web":
                document = get_web_documents(WebLoaderConfig(**loader_config))
            case "db":
                db_uri = get_connection_string()
                configs = [
                    DBLoaderConfig(uri=db_uri, queries=db_config.get('queries', []))
                    for db_config in loader_config
                ]
                document = get_db_documents(configs)
            case _:
                raise ValueError(f"Invalid loader type: {loader_type}")
        documents.extend(document)

    return documents
