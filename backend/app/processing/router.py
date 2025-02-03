from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from sqlalchemy.orm import Session
import asyncio
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from typing import Annotated
from app.processing.service import get_queue_status, mark_items_as_queued, start_processing_thread
from app.processing.schemas import ProcessingRequest, ProcessingStatusResponse
from app.api.utils import get_user_id
from app.datasources.file_manager.database.session import get_datasources_file_manager_session
from app.datasources.database.session import get_datasources_db_session
from app.settings.database.session import get_settings_db_session
from app.processing_stacks.database.session import get_processing_stacks_db_session
from app.api.websocket import StatusWebSocket

logger = logging.getLogger("uvicorn")

processing_router = r = APIRouter()

@r.post("", response_model=ProcessingStatusResponse)
async def processing_route(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_user_id)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)],
    datasources_db_session: Annotated[Session, Depends(get_datasources_db_session)],
    processing_stacks_db_session: Annotated[Session, Depends(get_processing_stacks_db_session)],
) -> ProcessingStatusResponse:
    """Add files or folders to generation queue and start processing if needed"""
    try:
        # Get the file manager db sessions for all datasources in the files to be processed
        file_manager_db_sessions = {}
        for item in request.items:
            # Extract the datasource name from the original path
            datasource_name = item.original_path.split("/")[0]
            file_manager_db_session = None
            if datasource_name not in file_manager_db_sessions:
                file_manager_db_session = get_datasources_file_manager_session(
                    user_id=user_id,
                    datasource_name=datasource_name,
                    datasources_db_session=datasources_db_session
                )
                file_manager_db_sessions[datasource_name] = file_manager_db_session
            else:
                file_manager_db_session = file_manager_db_sessions[datasource_name]

            # Process all items in the request
            mark_items_as_queued(
                processing_stacks_db_session=processing_stacks_db_session,
                file_manager_db_session=file_manager_db_session,
                user_id=user_id,
                items=[item]
            )

        # Start processing thread if needed
        start_processing_thread(
            user_id=user_id,
            file_manager_db_sessions=file_manager_db_sessions,
            datasources_db_session=datasources_db_session,
            settings_db_session=settings_db_session,
            processing_stacks_db_session=processing_stacks_db_session
        )

        return get_queue_status(user_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in processing endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/status", response_model=ProcessingStatusResponse)
async def get_processing_status_route(
    user_id: Annotated[str, Depends(get_user_id)],
) -> ProcessingStatusResponse:
    """Get the current status of the generation queue"""
    try:
        # Start processing thread if needed
        return get_queue_status(user_id)
    except Exception as e:
        logger.error(f"Error in get_processing_status_route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@r.websocket("/status/ws")
async def processing_status_websocket(
    websocket: WebSocket,
    user_id: Annotated[str, Depends(get_user_id)],
):
    """WebSocket endpoint for processing status updates"""
    # Convert ProcessingStatusResponse to dict before sending
    status_ws = StatusWebSocket(
        websocket, 
        lambda: get_queue_status(user_id)
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