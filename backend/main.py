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
    # Disable most logging in production
    #logging.basicConfig(level=logging.WARNING)
    #logger.setLevel(logging.WARNING)

import uvicorn
from app.api.routers import api_router
from app.observability import init_observability
from app.settings import init_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.database.init_db import change_superuser_password
from app.pull_ollama_models import pull_models

logger.info("Starting application initialization")

app = FastAPI()

logger.info("Initializing settings")
init_settings()
init_observability()

logger.info("Initializing database")
# Change the superuser password if it's not already set
change_superuser_password()

# Pull Ollama models if not already present
if os.getenv("MODEL_PROVIDER") == "ollama":
    logger.info("Starting Ollama model pull process")
    threading.Thread(target=pull_models, daemon=True).start()

if environment == "dev":
    logger.warning("Running in development mode - allowing CORS for all origins")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Redirect to documentation page when accessing base URL
    @app.get("/")
    async def redirect_to_docs():
        return RedirectResponse(url="/docs")

else:
    # Default origins
    default_origins = [
        "http://idapt-backend:8000", # Allow requests from other containers on the same docker network, typically the frontend container routed through the nginx proxy.
    ]

    # Get trusted origins from environment variable
    trusted_origins_str = os.getenv("TRUSTED_ORIGINS", "")
    trusted_origins = trusted_origins_str.split(",") if trusted_origins_str else []

    # Combine default and trusted origins
    all_origins = default_origins + [origin.strip() for origin in trusted_origins if origin.strip()]
    
    logger.info(f"Allowed origins: {all_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def mount_static_files(directory, path):
    if os.path.exists(directory):
        logger.info(f"Mounting static files '{directory}' at '{path}'")
        app.mount(
            path,
            StaticFiles(directory=directory, check_dir=False),
            name=f"{directory}-static",
        )


# Mount the data files to serve the file viewer
mount_static_files(DATA_DIR, "/api/files/data")
# Mount the output files from tools
mount_static_files("output", "/api/files/output")

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = True if environment == "dev" else False

    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload)
