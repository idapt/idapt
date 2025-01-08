import logging
import os
from contextlib import contextmanager

def configure_app_logging():
    environment = os.getenv("ENVIRONMENT", "prod")

    # Base configuration
    logging.basicConfig(
        level=logging.INFO if environment == "dev" else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure FastAPI application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if environment == "dev" else logging.INFO)

    # Configure uvicorn loggers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []  # Remove existing handlers
    uvicorn_logger.propagate = False  # Don't propagate to root logger
    
    # Add handler for uvicorn
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(logging.INFO if environment == "dev" else logging.INFO)

    # Set other loggers
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
      
    # Filter out health check logs from uvicorn
    logging.getLogger("uvicorn.access").addFilter(
        lambda record: "/api/health" not in record.getMessage()
    )

@contextmanager
def get_logger_context(name: str):
    yield logging.getLogger(name)

def get_logger(name: str):
    with get_logger_context(name) as logger:
        return logger
