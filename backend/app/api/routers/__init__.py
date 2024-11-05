from fastapi import APIRouter

from .health import health_router  # noqa: F401
from .chat import chat_router  # noqa: F401
from .chat_config import config_router  # noqa: F401
from .upload import file_upload_router  # noqa: F401
from .generate import generate_router  # noqa: F401
from .vault import vault_router  # noqa: F401
from .file_manager import file_manager_router  # noqa: F401

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(config_router, prefix="/chat/config", tags=["chat-config"])
api_router.include_router(file_upload_router, prefix="/chat/upload", tags=["chat-upload"])
api_router.include_router(generate_router, prefix="/generate", tags=["generate"])
api_router.include_router(vault_router, prefix="/vault", tags=["vault"])
api_router.include_router(file_manager_router, prefix="/file-manager", tags=["file-manager"])

# Dynamically adding additional routers if they exist
try:
    from .sandbox import sandbox_router  # type: ignore

    api_router.include_router(sandbox_router, prefix="/sandbox")
except ImportError:
    pass
