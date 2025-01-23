from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from sqlalchemy.orm import Session
import asyncio
from fastapi import WebSocket

from app.processing.service import get_queue_status, mark_items_as_queued
from app.processing.schemas import ProcessingRequest
from app.api.utils import get_user_id, get_file_manager_db_session

logger = logging.getLogger("uvicorn")

processing_router = r = APIRouter()

@r.post("")
async def processing_route(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
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
    session: Session = Depends(get_file_manager_db_session),
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
    session: Session = Depends(get_file_manager_db_session),
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