from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel, Field
from app.services import ServiceManager
from app.services.generate import GenerateService
from app.services.file_system import get_full_path_from_path
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

generate_router = r = APIRouter()

def get_generate_service():
    return ServiceManager.get_instance().generate_service

def get_db_session():
    return ServiceManager.get_instance().db_service.get_session()

class GenerateRequest(BaseModel):
    files: List[dict] = Field(..., example=[{
        "path": "path/to/file.txt",
        "transformations_stack_name_list": ["default", "titles"]
    }])

@r.post("")
async def generate(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    generate_service: GenerateService = Depends(get_generate_service),
    session: Session = Depends(get_db_session)
):
    """
    Add multiple files to the generation queue for processing.
    Returns immediately with queue status.
    """
    try:
        # Convert to full paths and maintain transformation stack names
        files = [{
            # The given path is not a full path as the frontend is not aware of the DATA_DIR
            "path": get_full_path_from_path(file["path"]),
            "transformations_stack_name_list": file.get("transformations_stack_name_list", "default")
        } for file in request.files]
        
        # Add to queue
        background_tasks.add_task(generate_service.add_batch_to_queue, files)

        return {
            "status": "queued",
            "message": f"Added {len(request.files)} files to generation queue",
            "total_files": len(request.files)
        }
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/generate/status")
async def get_generation_status(
    generate_service: GenerateService = Depends(get_generate_service)
):
    """Get the current status of the generation queue"""
    try:
        status = generate_service.get_queue_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))