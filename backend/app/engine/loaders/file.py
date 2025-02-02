# Legacy, unused
import os
import logging
from typing import Dict, List
from llama_parse import LlamaParse
from pydantic import BaseModel
from app.constants.data_dir import DATA_DIR
logger = logging.getLogger("uvicorn")

class FileLoaderConfig(BaseModel):
    use_llama_parse: bool = False
def llama_parse_parser():
    if os.getenv("LLAMA_CLOUD_API_KEY") is None:
        raise ValueError(
            "LLAMA_CLOUD_API_KEY environment variable is not set. "
            "Please set it in .env file or in your shell environment then run again!"
        )
    parser = LlamaParse(
        result_type="markdown",
        verbose=True,
        language="en",
        ignore_errors=False,
    )
    return parser

def llama_parse_extractor() -> Dict[str, LlamaParse]:
    from llama_parse.utils import SUPPORTED_FILE_TYPES
    parser = llama_parse_parser()
    return {file_type: parser for file_type in SUPPORTED_FILE_TYPES}
    
def get_file_documents(config: FileLoaderConfig, file_paths: List[str] = None):
    """Get documents from specified files or all files if none specified"""
    from llama_index.core.readers import SimpleDirectoryReader
    try:
        file_extractor = None
        if config.use_llama_parse:
            import nest_asyncio
            nest_asyncio.apply()
            file_extractor = llama_parse_extractor()
            
        # If specific files are provided, verify they exist in DATA_DIR
        if file_paths:
            valid_paths = []
            for path in file_paths:
                fs_path = os.path.join(DATA_DIR, path)
                if os.path.exists(fs_path):
                    valid_paths.append(fs_path)
                else:
                    logger.warning(f"File not found: {path}")
            
            if not valid_paths:
                return []
                
            reader = SimpleDirectoryReader(
                input_files=valid_paths,
                filename_as_id=True,
                raise_on_error=True,
                file_extractor=file_extractor,
            )
        # If no specific files are provided, load all files in DATA_DIR
        else:
            reader = SimpleDirectoryReader(
                DATA_DIR,
                recursive=True,
                filename_as_id=True,
                raise_on_error=True,
                file_extractor=file_extractor,
            )
            
        return reader.load_data()
    except Exception as e:
        import sys
        import traceback
        _, _, exc_traceback = sys.exc_info()
        function_name = traceback.extract_tb(exc_traceback)[-1].name
        if function_name == "_add_files":
            logger.warning(
                f"Failed to load file documents, error message: {e}. Return as empty document list."
            )
            return []
        else:
            raise e