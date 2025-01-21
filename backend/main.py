# flake8: noqa: E402
import logging
import os
from contextlib import asynccontextmanager
import time
from typing import Tuple
# Set up logging configuration
from app.api.logging import configure_app_logging
configure_app_logging()

logger = logging.getLogger("uvicorn")

from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
     
    yield  # Application runs here
    

def create_app() -> FastAPI:

    app = FastAPI(
        title="idapt API",
        lifespan=lifespan
    )

    environment = os.getenv("ENVIRONMENT", "prod")  # Default to 'prod' if not set so that we dont risk exposing the API to the public

    # Initialize observability for logging of this api
    if environment == "dev":
        from app.api.observability import init_observability
        init_observability()
    
    # Configure CORS
    from app.api.cors import configure_cors
    configure_cors(app, environment)
    
    # Mount static files
    #mount_static_files(app)
    
    # Include API router
    from app.api import api_router
    app.include_router(api_router, prefix="/api")
    
    return app

# TODO Implement this without using StaticFiles and only return a file if authenticated and authorized and it need to be stateless
#def mount_static_files(app: FastAPI):
#    def mount_directory(directory: str, path: str):
#        if os.path.exists(directory):
#            logger.info(f"Mounting static files '{directory}' at '{path}'")
#            app.mount(
#                path,
#                StaticFiles(directory=directory, check_dir=False),
#                name=f"{directory}-static",
#            )
#    
#    # Mount the data files to serve the file viewer
#    mount_directory(DATA_DIR, "/api/files/data")
#    # Mount the output files from tools
#    mount_directory("/data/.idapt/output", "/api/files/output")


# Create the app instance
app = create_app()

# Only run these in the main process, not in reloaded processes
if __name__ == "__main__":

    import uvicorn

    host_domain = "0.0.0.0" #os.getenv("HOST_DOMAIN", "0.0.0.0") # TODO Use the host domain
    api_port = int(os.getenv("API_PORT", 8000))
    environment = os.getenv("ENVIRONMENT", "prod")  # Default to 'prod' if not set so that we dont risk set dev env in prod
    deployment_type = os.getenv("DEPLOYMENT_TYPE", "self-hosted")

    # Setup the backend certs
    from app.api.certs import setup_backend_certs
    ssl_keyfile_path, ssl_certfile_path = setup_backend_certs(host_domain, deployment_type)

    if environment == "dev":
        logger.info("Starting in development mode with hot reload")
        uvicorn.run(
            "main:app",
            host=host_domain,
            port=api_port,
            reload=True,
            reload_dirs=['app'],
            reload_includes=['*.py'],
            reload_excludes=['__pycache__'],
            log_level="info",
            ssl_keyfile=ssl_keyfile_path,
            ssl_certfile=ssl_certfile_path
        )
    else:
        logger.info("Starting in production mode")
        uvicorn.run(
            "main:app",
            host=host_domain,
            port=api_port,
            reload=False,
            workers=4,
            log_level="error",
            ssl_keyfile=ssl_keyfile_path,
            ssl_certfile=ssl_certfile_path
        )
