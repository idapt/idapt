from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel
from app.services.generate import GenerateService
from app.services.file_system import FileSystemService
from app.database.connection import get_db_session
from sqlalchemy.orm import Session

generate_router = r = APIRouter()
logger = logging.getLogger(__name__)
file_system_service = FileSystemService()

class GenerateRequest(BaseModel):
    file_paths: List[str]

class BatchGenerateRequest(BaseModel):
    file_ids: List[int]

# TODO Temporary endpoint to add files to the generation queue by file paths, switch to file_ids
@r.post("")
async def generate(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session)
):
    """
    Add multiple files to the generation queue for processing.
    Returns immediately with queue status.
    """
    try:
        # Convert to full paths
        file_paths = [file_system_service.get_full_path(file_path) for file_path in request.file_paths]
        # Add to queue
        background_tasks.add_task(GenerateService.add_batch_to_queue, file_paths)

        return {
            "status": "queued",
            "message": f"Added {len(request.file_paths)} files to generation queue",
            "total_files": len(request.file_paths)
        }
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.post("/generate/{file_id}")
async def generate(
    file_id: int
):
    """
    Add a file to the generation queue for processing.
    Returns the queue position of the added file.
    """
    try:
        position = await GenerateService.add_to_queue(file_id)
        return {
            "status": "queued",
            "message": f"File added to generation queue at position {position}",
            "queue_position": position
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/generate/status")
async def get_generation_status():
    """Get the current status of the generation queue"""
    try:
        status = GenerateService.get_queue_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))