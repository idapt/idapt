from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, WebSocket
from app.api.utils import get_user_id
from app.settings.database.session import get_settings_db_session
from sqlalchemy.orm import Session
import logging
from app.api.websocket import StatusWebSocket
from fastapi import WebSocketDisconnect
from app.ollama_status.schemas import OllamaStatusResponse
from app.ollama_status.service import can_process
from typing import Annotated

logger = logging.getLogger("uvicorn")

ollama_status_router = r = APIRouter()

@r.get("", response_model=OllamaStatusResponse)
async def get_ollama_status_route(
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_user_id)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)],
):
    """Get the current status of Ollama model downloads"""
    try:
        #logger.info(f"Getting Ollama status for user {user_id}")
        if not await can_process(settings_db_session, True): # Don't download models, it will be done on file processing
            return {"is_downloading": True}
        else:
            return {"is_downloading": False}
    except Exception as e:
        logger.error(f"Error in get_ollama_status_route: {str(e)}")
        # Return a http 500 error with the error message
        raise HTTPException(status_code=500, detail=str(e))


@r.websocket("/ws")
async def ollama_status_websocket_route(
    websocket: WebSocket,
    user_id: Annotated[str, Depends(get_user_id)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)]
):
    """WebSocket endpoint for Ollama status updates"""
    async def get_status():
        is_downloading = not await can_process(settings_db_session, False)
        return {"is_downloading": is_downloading}
    
    status_ws = StatusWebSocket(websocket, get_status)
    await status_ws.accept()
    
    async with status_ws.status_loop():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect as e:
            if e.code not in (1000, 1001, 1012):  # Normal close codes
                logger.error(f"WebSocket disconnected with code {e.code}")
        except Exception as e:
            logger.error(f"Unexpected error in ollama_status_websocket: {str(e)}")
