from typing import List
import logging
from app.engine.generate import generate_files_embeddings

logger = logging.getLogger(__name__)

class GenerateService:
    @staticmethod
    async def generate_embeddings(file_paths: List[str]) -> None:
        """
        Generate embeddings for the given file paths
        """
        logger.info("Starting the datasource generation process.")
        try:
            generate_files_embeddings(file_paths)
            logger.info("Datasource generation completed successfully.")
        except Exception as e:
            logger.error(f"Error generating datasource: {e}", exc_info=True)
            raise 