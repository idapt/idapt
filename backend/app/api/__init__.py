from fastapi import APIRouter

# Initialize routers

from app.auth.router import auth_router  # noqa: F401
from app.chat.router import chat_router  # noqa: F401
from app.settings.router import settings_router  # noqa: F401
from app.datasources.router import datasources_router  # noqa: F401
from app.processing.router import processing_router  # noqa: F401
from app.processing_stacks.router import processing_stacks_router  # noqa: F401
from app.ollama_status.router import ollama_status_router  # noqa: F401
from app.health.router import health_router  # noqa: F401


# Build the api endpoints
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(datasources_router, prefix="/datasources", tags=["datasources"])
api_router.include_router(processing_router, prefix="/processing", tags=["processing"])
api_router.include_router(processing_stacks_router, prefix="/stacks", tags=["stacks"])
api_router.include_router(ollama_status_router, prefix="/ollama-status", tags=["ollama-status"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
