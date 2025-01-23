from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, WebSocket
from app.ollama_status.service import can_process
from app.api.utils import get_user_id, get_file_manager_db_session
from sqlalchemy.orm import Session
import logging
import asyncio

logger = logging.getLogger("uvicorn")

ollama_status_router = r = APIRouter()

@r.get("")
async def get_ollama_status_route(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
):
    """Get the current status of Ollama model downloads"""
    try:
        #logger.info(f"Getting Ollama status")
        if not await can_process(session, False): # Don't download models, it will be done on file processing
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
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
):
    """WebSocket endpoint for Ollama status updates"""
    await websocket.accept()
    
    prev_status = None
    try:
        while True:
            # Check status every 2 seconds
            current_status = not await can_process(session, False)
            
            # Only send if status changed
            if current_status != prev_status:
                await websocket.send_json({"is_downloading": current_status})
                prev_status = current_status
            
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Error in ollama_status_websocket: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass
