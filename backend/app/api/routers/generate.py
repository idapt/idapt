from fastapi import APIRouter, WebSocket, HTTPException, Depends
import logging
from typing import List
from pydantic import BaseModel, Field
from app.services.generate import get_queue_status
from app.services.file_system import get_full_path_from_path
from app.services.db_file import update_db_file_status
from app.database.models import FileStatus
from app.services.database import get_session
from sqlalchemy.orm import Session
import asyncio
logger = logging.getLogger(__name__)

generate_router = r = APIRouter()

def get_db_session():
    with get_session() as session:
        yield session

class GenerateRequest(BaseModel):
    files: List[dict] = Field(..., example=[{
        "path": "path/to/file.txt",
        "transformations_stack_name_list": ["default", "titles"]
    }])

@r.post("")
async def generate_route(
    request: GenerateRequest,
    session: Session = Depends(get_db_session)
):
    """Add files to generation queue and start processing if needed"""
    try:
        logger.info(f"Marking {len(request.files)} files as queued")

        # Mark the file as queued in the database and add thier stacks to process with
        for file in request.files:
            update_db_file_status(
                session,
                # The given path is not a full path as the frontend is not aware of the DATA_DIR
                get_full_path_from_path(file["path"]),
                FileStatus.QUEUED,
                file.get("transformations_stack_name_list", ["default"])
            )

        status = get_queue_status(session)
                
        return {
            "status": "queued",
            "message": f"Added {len(request.files)} files to generation queue",
            "queue_status": status
        }
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/status")
async def get_generation_status_route(
    session: Session = Depends(get_db_session)
):
    """Get the current status of the generation queue"""
    try:
        status = get_queue_status(session)
        logger.info(f"Generation status: {status}")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#@r.websocket("/status/ws")
#async def generate_status_websocket(
#    websocket: WebSocket,
#    session: Session = Depends(get_db_session)
#):
#    """WebSocket endpoint for generation status updates"""
#    while True:
#        await asyncio.sleep(1)
#        # TODO Reimplement this, either use db on update or ...
#    #try:
#    #    await GenerateService().connect(websocket)
#    #    while True:
#    #    try:
#    #        # Keep connection alive and wait for client messages
#    #        await websocket.receive_text()
#    #    except Exception:
#    #        break
#    #finally:
#    #    await generate_service.disconnect(websocket) 
#