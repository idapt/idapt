from fastapi import APIRouter, WebSocket, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel, Field
from app.services import ServiceManager
from app.services.generate import GenerateService
from app.services.file_system import get_full_path_from_path
from sqlalchemy.orm import Session
from functools import lru_cache

logger = logging.getLogger(__name__)

generate_router = r = APIRouter()

@lru_cache()
def get_service_manager():
    return ServiceManager.get_instance()

def get_generate_service():
    return get_service_manager().generate_service

def get_db_session():
    with ServiceManager.get_instance().db_service.get_session() as session:
        yield session

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
        logger.info(f"Trigger Generating {len(request.files)} files")
        # Convert to full paths and maintain transformation stack names
        files = [{
            # The given path is not a full path as the frontend is not aware of the DATA_DIR
            "path": get_full_path_from_path(file["path"]),
            "transformations_stack_name_list": file.get("transformations_stack_name_list")
        } for file in request.files]
        
        # Add to queue
        # Use background tasks to avoid blocking the main thread
        background_tasks.add_task(generate_service.add_files_to_queue, files, session)

        return {
            "status": "queued",
            "message": f"Added {len(request.files)} files to generation queue",
            "total_files": len(request.files)
        }
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/status")
async def get_generation_status(
    generate_service: GenerateService = Depends(get_generate_service)
):
    """Get the current status of the generation queue"""
    try:
        status = generate_service.get_queue_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@r.websocket("/status/ws")
async def generate_status_websocket(
    websocket: WebSocket,
    generate_service: GenerateService = Depends(get_generate_service)
):
    """WebSocket endpoint for generation status updates"""
    try:
        await generate_service.connect(websocket)
        while True:
            try:
                # Keep connection alive and wait for client messages
                await websocket.receive_text()
            except Exception:
                break
    finally:
        await generate_service.disconnect(websocket) 