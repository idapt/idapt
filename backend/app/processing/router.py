from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from sqlalchemy.orm import Session
import asyncio
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from app.processing.service import get_queue_status, mark_items_as_queued, start_processing_if_needed_and_get_queue_status
from app.processing.schemas import ProcessingRequest, ProcessingStatusResponse
from app.api.utils import get_user_id, get_file_manager_db_session
from app.api.websocket import StatusWebSocket

logger = logging.getLogger("uvicorn")

processing_router = r = APIRouter()

@r.post("", response_model=ProcessingStatusResponse)
async def processing_route(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
) -> ProcessingStatusResponse:
    """Add files or folders to generation queue and start processing if needed"""
    try:
        # Process all items in the request
        mark_items_as_queued(session, user_id, request.items)

        # Start processing thread if needed
        return start_processing_if_needed_and_get_queue_status(session, user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in processing endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/status", response_model=ProcessingStatusResponse)
async def get_processing_status_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
) -> ProcessingStatusResponse:
    """Get the current status of the generation queue"""
    try:
        # Start processing thread if needed
        return start_processing_if_needed_and_get_queue_status(session, user_id)
    except Exception as e:
        logger.error(f"Error in get_processing_status_route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@r.websocket("/status/ws")
async def processing_status_websocket(
    websocket: WebSocket,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
):
    """WebSocket endpoint for processing status updates"""
    # Convert ProcessingStatusResponse to dict before sending
    status_ws = StatusWebSocket(
        websocket, 
        lambda: start_processing_if_needed_and_get_queue_status(session, user_id).model_dump()
    )
    await status_ws.accept()
    
    async with status_ws.status_loop():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect as e:
            if e.code not in (1000, 1001, 1012):  # Normal close codes
                logger.error(f"WebSocket disconnected with code {e.code}")
        except Exception as e:
            logger.error(f"Unexpected error in processing_status_websocket: {str(e)}")