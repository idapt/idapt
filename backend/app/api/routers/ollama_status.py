from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from app.services.ollama_status import can_process
from app.settings.models import AppSettings
from app.settings.manager import get_app_settings
from app.api.logging import get_logger

ollama_status_router = r = APIRouter()

@r.get("")
async def get_ollama_status_route(
    background_tasks: BackgroundTasks,
    app_settings: AppSettings = Depends(get_app_settings),
):
    """Get the current status of Ollama model downloads"""
    try:
        if not await can_process(app_settings, background_tasks):
            return {"is_downloading": True}
        else:
            return {"is_downloading": False}
    except Exception as e:
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

