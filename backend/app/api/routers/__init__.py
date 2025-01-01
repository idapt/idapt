from fastapi import APIRouter

# Initialize services and routers in the right order

# Llama index endpoints before
from app.api.routers.chat import chat_router  # noqa: F401
from app.api.routers.chat_config import config_router  # noqa: F401
from app.api.routers.upload import file_upload_router  # noqa: F401

# App settings
from app.api.routers.settings import settings_router  # noqa: F401

# File manager
from app.api.routers.file_manager import file_manager_router  # noqa: F401

# Datasources needs to be initialized after file manager
from app.api.routers.datasources import datasources_router  # noqa: F401

# Generate
from app.api.routers.generate import generate_router  # noqa: F401

# Ollama status
from app.api.routers.ollama_status import ollama_status_router  # noqa: F401

from app.api.routers.health import health_router  # noqa: F401


# Build the api endpoints
api_router = APIRouter()
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(config_router, prefix="/chat/config", tags=["chat-config"])
api_router.include_router(file_upload_router, prefix="/chat/upload", tags=["chat-upload"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(file_manager_router, prefix="/file-manager", tags=["file-manager"])
api_router.include_router(datasources_router, prefix="/datasources", tags=["datasources"])
api_router.include_router(generate_router, prefix="/generate", tags=["generate"])
api_router.include_router(ollama_status_router, prefix="/ollama-status", tags=["ollama-status"])
# Init health at the end when everything is started
api_router.include_router(health_router, prefix="/health", tags=["health"])
