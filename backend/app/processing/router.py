from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from sqlalchemy.orm import Session
import asyncio
from fastapi import WebSocket

from app.processing.service import get_queue_status, mark_items_as_queued
from app.processing.schema import ProcessingRequest
from app.database.service import get_db_session
from app.api.utils import get_user_id
from app.database.models import File, Folder
from app.file_manager.router import decode_path_safe
from app.file_manager.service.llama_index import delete_files_in_folder_recursive_from_llama_index, delete_file_llama_index
from app.file_manager.utils import validate_path

logger = logging.getLogger("uvicorn")

processing_router = r = APIRouter()

@r.post("")
async def processing_route(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Add files or folders to generation queue and start processing if needed"""
    try:
        # Process all items in the request
        mark_items_as_queued(session, user_id, request.items)

        # Get the current status of the queue
        status = get_queue_status(session)

        return {
            "status": "queued",
            "message": f"Added files to generation queue",
            "queue_status": status
        }
    except HTTPException:
        raise
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

@r.delete("/processed-data/{encoded_original_path}")
async def delete_processed_data_route(
    encoded_original_path: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
    original_path: str = Depends(decode_path_safe)
):
    try:
        logger.info(f"Deleting processed data for user {user_id} and path {original_path}")

        # Validate path
        validate_path(original_path)

        # Check if it's a file
        file = session.query(File).filter(File.original_path == original_path).first()
        if file:
            # Delete llama index data
            delete_file_llama_index(session=session, user_id=user_id, file=file)

            session.commit()
            return {"success": True}
            
        # If not a file, check if it's a folder
        folder = session.query(Folder).filter(Folder.original_path == original_path).first()
        if folder:
            delete_files_in_folder_recursive_from_llama_index(session=session, user_id=user_id, full_folder_path=folder.path)
            return {"success": True}
            
        raise HTTPException(status_code=404, detail="Item not found")
        
    except Exception as e:
        logger.error(f"Error deleting processed data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete processed data")