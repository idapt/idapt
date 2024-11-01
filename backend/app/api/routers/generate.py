from fastapi import APIRouter, HTTPException
import logging
from app.engine.generate import generate_datasource

generate_router = r = APIRouter()
logger = logging.getLogger(__name__)

@r.post("")
async def generate():
    """
    Generate the datasource by running the ingestion pipeline.
    This will process all configured data sources and update the vector store.
    """
    logger.info("Starting the datasource generation process.")
    try:
        generate_datasource()
        logger.info("Datasource generation completed successfully.")
        return {"status": "success", "message": "Successfully generated datasource"}
    except Exception as e:
        logger.error(f"Error generating datasource: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
