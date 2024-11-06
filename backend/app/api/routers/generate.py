from fastapi import APIRouter, HTTPException
import logging
from typing import List
from pydantic import BaseModel
from app.engine.generate import generate_files_embeddings

generate_router = r = APIRouter()
logger = logging.getLogger(__name__)

class GenerateRequest(BaseModel):
    file_paths: List[str]

@r.post("")
async def generate(request: GenerateRequest):
    """
    Generate the datasource by running the ingestion pipeline for specified files.
    This will process the given files and update the vector store.
    """
    logger.info("Starting the datasource generation process.")
    try:
        generate_files_embeddings(request.file_paths)
        logger.info("Datasource generation completed successfully.")
        return {"status": "success", "message": "Successfully generated datasource"}
    except Exception as e:
        logger.error(f"Error generating datasource: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
