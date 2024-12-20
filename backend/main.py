# flake8: noqa: E402
from app.config import DATA_DIR
from dotenv import load_dotenv

load_dotenv()

import logging
import os

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

logger.info("Starting application initialization")

def create_app() -> FastAPI:

    app = FastAPI()

    from app.observability import init_observability
    init_observability()
    
    # Initialize the application settings using SettingsManager, as the settings are new, it will update the dependent services
    from app.settings.manager import AppSettingsManager
    AppSettingsManager.get_instance().settings

    # Initialize the database
    from app.database.init_db import initialize_database
    initialize_database()

    # Initialize all services
    from app.services import ServiceManager
    ServiceManager.get_instance()
    
    # Configure CORS
    configure_cors(app)
    
    # Mount static files
    mount_static_files(app)
    
    # Include API router to init the API endpoints
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
            allow_origins=["http://idapt-nginx:3030"],
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
    mount_directory("output", "/api/files/output")

# Create the app instance
app = create_app()

# Only run these in the main process, not in reloaded processes
if __name__ == "__main__":
        
    app_host = "0.0.0.0" #os.getenv("HOST_DOMAIN", "0.0.0.0") # For now use 0.0.0.0
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = environment == "dev"
    
    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload, log_level="info")
