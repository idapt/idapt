import logging
import os
from contextlib import contextmanager

def configure_app_logging():
    environment = os.getenv("ENVIRONMENT", "prod")

    # Base configuration
    logging.basicConfig(
        level=logging.DEBUG if environment == "dev" else logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure FastAPI application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if environment == "dev" else logging.ERROR)

    # Configure uvicorn loggers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []  # Remove existing handlers
    uvicorn_logger.propagate = False  # Don't propagate to root logger

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING if environment == "dev" else logging.WARNING)
    
    # Add handler for uvicorn
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(logging.DEBUG if environment == "dev" else logging.ERROR)

    # Set other loggers
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
      
    # Filter out health check logs from uvicorn
    logging.getLogger("uvicorn.access").addFilter(
        lambda record: "/api/health" not in record.getMessage()
    )
    # Filter out ollama status logs from uvicorn
    logging.getLogger("uvicorn.access").addFilter(
        lambda record: "/api/ollama-status" not in record.getMessage()
    )
    # Filter out generate status logs from uvicorn
    logging.getLogger("uvicorn.access").addFilter(
        lambda record: "/api/generate/status" not in record.getMessage()
    )    
