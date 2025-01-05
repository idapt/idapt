from fastapi import APIRouter, WebSocket, Depends
from app.services.ollama_status import OllamaStatusService

ollama_status_router = r = APIRouter()

def get_ollama_status_service():
    return OllamaStatusService() 

@r.get("")
async def get_ollama_status_route(
    status_service = Depends(get_ollama_status_service)
):
    """Get the current status of Ollama model downloads"""
    return {"is_downloading": status_service.get_status()}

@r.websocket("/ws")
async def ollama_status_websocket_route(
    websocket: WebSocket,
    status_service = Depends(get_ollama_status_service)
):
    """WebSocket endpoint for Ollama status updates"""
    try:
        await status_service.connect(websocket)
        while True:
            try:
                await websocket.receive_text()
            except Exception:
                break
    finally:
        await status_service.disconnect(websocket) 

