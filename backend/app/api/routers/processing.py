from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
import os
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.processing import get_queue_status, process_queued_files, should_start_processing, mark_file_as_queued
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

class ProcessingFolderRequest(BaseModel):
    folder_path: str = Field(..., example="path/to/folder")
    transformations_stack_name_list: List[str] = Field(..., example=["default", "titles"])

@r.post("")
async def processing_route(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
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
            background_tasks.add_task(process_queued_files, session, user_id)

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

@r.post("/folder")
async def process_folder_route(
    request: ProcessingFolderRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    """Add all files in a folder to generation queue and start processing if needed"""
    try:
        full_folder_path = get_full_path_from_path(request.folder_path, user_id)
        
        if not os.path.exists(full_folder_path):
            raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
        
        if not os.path.isdir(full_folder_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.folder_path}")

        # Get all files in the folder
        files = []
        for root, _, filenames in os.walk(full_folder_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, get_full_path_from_path("", user_id))
                files.append({
                    "path": relative_path,
                    "transformations_stack_name_list": request.transformations_stack_name_list
                })

        # Mark all files as queued
        for file in files:
            mark_file_as_queued(
                session,
                get_full_path_from_path(file["path"], user_id),
                file["transformations_stack_name_list"]
            )

        # Start processing if needed
        if should_start_processing(session):
            background_tasks.add_task(process_queued_files, session, user_id)

        status = get_queue_status(session)

        return {
            "status": "queued",
            "message": f"Added {len(files)} files from folder to generation queue",
            "queue_status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_folder endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))