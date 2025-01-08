from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel, Field
from app.services.generate import get_queue_status, process_queued_files, should_start_processing
from app.services.file_system import get_full_path_from_path
from app.services.db_file import update_db_file_status
from app.settings.models import AppSettings
from app.settings.manager import get_app_settings
from app.database.models import FileStatus
from app.services.database import get_db_session
from sqlalchemy.orm import Session
import asyncio
logger = logging.getLogger("uvicorn")

generate_router = r = APIRouter()

class GenerateRequest(BaseModel):
    files: List[dict] = Field(..., example=[{
        "path": "path/to/file.txt",
        "transformations_stack_name_list": ["default", "titles"]
    }])

@r.post("")
async def generate_route(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    app_settings: AppSettings = Depends(get_app_settings),
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

        # Start processing the files in the background
        # TODO Move the generate service to a separate api running on its own server
        if should_start_processing(session):    
            logger.info("Starting processing of queued files")
            background_tasks.add_task(process_queued_files, session, app_settings)

        # Get the current status of the queue
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
        #logger.info(f"Getting generation status")
        status = get_queue_status(session)
        return status
    except Exception as e:
        logger.error(f"Error in get_generation_status_route: {str(e)}")
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