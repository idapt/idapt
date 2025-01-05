from fastapi import APIRouter, WebSocket, Depends
from app.services.ollama_status import can_process

ollama_status_router = r = APIRouter()

@r.get("")
async def get_ollama_status_route():
    """Get the current status of Ollama model downloads"""

    if not can_process():
        return {"is_downloading": True}
    else:
        return {"is_downloading": False}

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

