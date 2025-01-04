# flake8: noqa: E402
from app.config import DATA_DIR
from dotenv import load_dotenv

load_dotenv()

import logging
import os
from contextlib import asynccontextmanager

# Set up logging configuration early
environment = os.getenv("ENVIRONMENT", "prod")  # Default to 'prod' if not set so that we dont risk exposing the API to the public

logger = logging.getLogger(__name__)

if environment == "dev":
    # Configure more verbose logging for development
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger.setLevel(logging.INFO)
    # Set log levels for other specific loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)

else:
    # Keep detailed logging for production for now
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger.setLevel(logging.INFO)
    # Set log levels for specific loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)

# Filter out health check logs from uvicorn
logging.getLogger("uvicorn.access").addFilter(
    lambda record: "/api/health" not in record.getMessage()
)

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

logger.info(f"Starting application initialization in process {os.getpid()}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Startup
    current_pid = os.getpid()
    logger.info(f"Starting up application in process {current_pid}")
    
    # Initialize observability first
    from app.observability import init_observability
    init_observability()
    
    # Initialize settings
    from app.settings.manager import AppSettingsManager
    AppSettingsManager.get_instance().settings
    
    # Initialize database
    from app.database.init_db import initialize_database
    initialize_database()
    
    # Initialize default datasources
    from app.services.datasource import _init_default_datasources
    from app.services.database import get_session
    with get_session() as session:
        _init_default_datasources(session)
    
    # Initialize services
    from app.services import ServiceManager
    service_manager = ServiceManager.get_instance()
    logger.info(f"Services initialized in process {current_pid}")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info(f"Shutting down application in process {current_pid}")
    # Add any cleanup code here

def create_app() -> FastAPI:
    app = FastAPI(
        title="idapt API",
        lifespan=lifespan
    )
    
    # Configure CORS
    configure_cors(app)
    
    # Mount static files
    mount_static_files(app)
    
    # Include API router
    from app.api.routers import api_router
    app.include_router(api_router, prefix="/api")
    
    return app

def configure_cors(app: FastAPI):
    if environment == "dev":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/")
        async def redirect_to_docs():
            return RedirectResponse(url="/docs")
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[f"http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

def mount_static_files(app: FastAPI):
    def mount_directory(directory: str, path: str):
        if os.path.exists(directory):
            logger.info(f"Mounting static files '{directory}' at '{path}'")
            app.mount(
                path,
                StaticFiles(directory=directory, check_dir=False),
                name=f"{directory}-static",
            )
    
    # Mount the data files to serve the file viewer
    mount_directory(DATA_DIR, "/api/files/data")
    # Mount the output files from tools
    mount_directory("/data/.idapt/output", "/api/files/output")

# Create the app instance
app = create_app()


# Only run these in the main process, not in reloaded processes
if __name__ == "__main__":

    app_host = "0.0.0.0" #os.getenv("HOST_DOMAIN", "0.0.0.0") # For now use 0.0.0.0
    app_port = 8000
    
    if environment == "dev":
        logger.info("Starting in development mode with hot reload")
        uvicorn.run(
            "main:app",
            host=app_host,
            port=app_port,
            reload=True,
            workers=1,
            reload_includes=['*.py'],
            reload_dirs=['app'],
            log_level="info"
        )
    else:
        logger.info("Starting in production mode")
        uvicorn.run(
            "main:app",
            host=app_host,
            port=app_port,
            reload=False,
            workers=1,
            log_level="info"
        )