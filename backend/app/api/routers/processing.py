from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.processing import get_queue_status, process_queued_files, should_start_processing, mark_file_as_queued
from app.settings.models import AppSettings
from app.settings.manager import get_app_settings
from app.services.database import get_db_session
from app.api.dependencies import get_user_id
from app.services.file_system import get_full_path_from_path


logger = logging.getLogger("uvicorn")

processing_router = r = APIRouter()

class ProcessingRequest(BaseModel):
    files: List[dict] = Field(..., example=[{
        "path": "path/to/file.txt",
        "transformations_stack_name_list": ["default", "titles"]
    }])

@r.post("")
async def processing_route(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
    app_settings: AppSettings = Depends(get_app_settings),
):
    """Add files to generation queue and start processing if needed"""
    try:
        logger.info(f"Marking {len(request.files)} files as queued for user {user_id}")

        # Mark the file as queued in the database and add thier stacks to process with
        for file in request.files:
            mark_file_as_queued(
                session,
                get_full_path_from_path(file["path"], user_id), # The given path by the frontend is not a full path as the frontend is not aware of the DATA_DIR and the user_id
                file.get("transformations_stack_name_list")
            )

        # Start processing the files in the background
        # TODO Move the processing service to a separate api running on its own server
        if should_start_processing(session):    
            logger.info(f"Starting processing of queued files for user {user_id}")
            background_tasks.add_task(process_queued_files, session, user_id, app_settings)

        # Get the current status of the queue
        status = get_queue_status(session)

        return {
            "status": "queued",
            "message": f"Added {len(request.files)} files to generation queue",
            "queue_status": status
        }
    except Exception as e:
        logger.error(f"Error in processing endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/status")
async def get_processing_status_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
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
#async def processing_status_websocket(
#    websocket: WebSocket,
#    session: Session = Depends(get_db_session),
#    user_id: str = Depends(get_user_id),
#):
#    """WebSocket endpoint for generation status updates"""
#    while True:
#        await asyncio.sleep(1)
#        # TODO Reimplement this, either use db on update or ...