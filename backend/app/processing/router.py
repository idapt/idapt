from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import asyncio
from fastapi import WebSocket

from app.processing.service import get_queue_status, process_queued_files, should_start_processing, mark_file_as_queued
from app.database.service import get_db_session
from app.api.utils import get_user_id
from app.file_manager.file_system import get_existing_sanitized_path
from app.database.models import File, Folder
from app.file_manager.router import decode_path_safe
from app.file_manager.llama_index import delete_files_in_folder_recursive_from_llama_index, delete_file_llama_index

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
                get_existing_sanitized_path(session, file["path"]),
                file.get("transformations_stack_name_list")
            )

        # Start processing the files in the background
        # TODO Move the processing service to a separate api running on its own server
        # TODO Split the files to process by datasource and enhance all should_start_processing to check if all datasources are ready
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

@r.websocket("/status/ws")
async def processing_status_websocket(
    websocket: WebSocket,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """WebSocket endpoint for processing status updates"""
    await websocket.accept()
    
    prev_status = None
    try:
        while True:
            # Check status every 2 seconds
            current_status = get_queue_status(session)
            
            # Only send if status changed
            if current_status != prev_status:
                await websocket.send_json(current_status)
                prev_status = current_status
            
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Error in processing_status_websocket: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass

@r.post("/folder")
async def process_folder_route(
    request: ProcessingFolderRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    """Add all files in a folder to generation queue and start processing if needed"""
    try:
        full_folder_path = get_existing_sanitized_path(session, request.folder_path)
        
        if not session.query(Folder).filter(Folder.path == full_folder_path).first():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.folder_path}")

        # Get all files in the folder from the database
        files = session.query(File).filter(File.path.like(f"{full_folder_path}%")).all()
        for file in files:
            mark_file_as_queued(
                session,
                file.path,
                request.transformations_stack_name_list
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

@r.delete("/processed-data/{encoded_original_path}")
async def delete_processed_data_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        original_path = decode_path_safe(encoded_original_path)
        full_path = get_existing_sanitized_path(session=session, original_path=original_path)
        
        # Check if it's a file
        file = session.query(File).filter(File.path == full_path).first()
        if file:
            # Delete llama index data
            delete_file_llama_index(session=session, user_id=user_id, file=file)

            session.commit()
            return {"success": True}
            
        # If not a file, check if it's a folder
        folder = session.query(Folder).filter(Folder.path == full_path).first()
        if folder:
            delete_files_in_folder_recursive_from_llama_index(session=session, user_id=user_id, full_folder_path=full_path)
            return {"success": True}
            
        raise HTTPException(status_code=404, detail="Item not found")
        
    except Exception as e:
        logger.error(f"Error deleting processed data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete processed data")