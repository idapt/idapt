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
    
    # Mount routers and static files
    app.include_router(api_router)
    
    return app

def configure_cors(app: FastAPI):
    if os.getenv("ENVIRONMENT") == "dev":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Production CORS settings
        default_origins = ["http://idapt-backend:8000"]
        trusted_origins = os.getenv("TRUSTED_ORIGINS", "").split(",")
        all_origins = default_origins + [o.strip() for o in trusted_origins if o.strip()]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=all_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

# Create the app instance
app = create_app()

# Only run these in the main process, not in reloaded processes
if __name__ == "__main__":
    # Pull Ollama models if needed
    if os.getenv("MODEL_PROVIDER") == "ollama":
        threading.Thread(target=pull_models, daemon=True).start()
        
    uvicorn.run(app, host="0.0.0.0", port=8000)
