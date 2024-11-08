# flake8: noqa: E402
from app.config import DATA_DIR
from dotenv import load_dotenv

load_dotenv()

import logging
import os
import threading

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
else:
    # Keep detailed logging for production for now
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger.setLevel(logging.INFO)

import uvicorn
from app.api.routers import api_router
from app.observability import init_observability
from app.settings import init_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.database.init_db import initialize_database
from app.pull_ollama_models import pull_models

logger.info("Starting application initialization")

def create_app() -> FastAPI:
    app = FastAPI()
    
    # Initialize core components
    init_settings()
    init_observability()
    initialize_database()
    
    # Configure CORS
    configure_cors(app)
    
    # Mount static files
    mount_static_files(app)
    
    # Include API router
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
        default_origins = ["http://idapt-backend:8000"]
        trusted_origins = os.getenv("TRUSTED_ORIGINS", "").split(",")
        all_origins = default_origins + [o.strip() for o in trusted_origins if o.strip()]
        
        logger.info(f"Allowed origins: {all_origins}")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=all_origins,
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
    # Pull Ollama models if needed
    if os.getenv("MODEL_PROVIDER") == "ollama":
        threading.Thread(target=pull_models, daemon=True).start()
        
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = environment == "dev"
    
    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload)
