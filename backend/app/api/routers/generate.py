from fastapi import APIRouter, HTTPException
import logging
from typing import List
from pydantic import BaseModel
from app.services.generate import GenerateService

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
    try:
        await GenerateService.generate_embeddings(request.file_paths)
        return {"status": "success", "message": "Successfully generated datasource"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
