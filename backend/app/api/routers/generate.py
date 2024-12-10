from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel, Field
from app.services.generate import GenerateService
from app.services.file_system import get_full_path_from_path
from app.database.connection import get_db_session
from sqlalchemy.orm import Session

generate_router = r = APIRouter()
logger = logging.getLogger(__name__)

class GenerateRequest(BaseModel):
    files: List[dict] = Field(..., example=[{
        "path": "path/to/file.txt",
        "transformations_stack_name_list": ["default", "titles"]
    }])

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
        # Convert to full paths and maintain transformation stack names
        files = [{
            "path": get_full_path_from_path(file["path"]),
            "transformations_stack_name_list": file.get("transformations_stack_name_list", "default")
        } for file in request.files]
        
        # Add to queue
        background_tasks.add_task(GenerateService.add_batch_to_queue, files)

        return {
            "status": "queued",
            "message": f"Added {len(request.files)} files to generation queue",
            "total_files": len(request.files)
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