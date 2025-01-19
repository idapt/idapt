from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from app.services.ollama_status import can_process
from app.api.dependencies import get_user_id
from sqlalchemy.orm import Session
from app.services.database import get_db_session
import logging

logger = logging.getLogger("uvicorn")

ollama_status_router = r = APIRouter()

@r.get("")
async def get_ollama_status_route(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
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

#@r.websocket("/ws")
#async def ollama_status_websocket_route(
#    websocket: WebSocket):
#    """WebSocket endpoint for Ollama status updates"""
#    try:
#        await status_service.connect(websocket)
#        while True:
#            try:
#                await websocket.receive_text()
#            except Exception:
#                break
#    finally:
#        await status_service.disconnect(websocket) 

