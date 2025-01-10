# flake8: noqa: E402
import logging
import os
from contextlib import asynccontextmanager
# Set up logging configuration
from app.api.logging import configure_app_logging
configure_app_logging()

logger = logging.getLogger("uvicorn")

from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""

    # Initialize observability for logging of this api
    from app.observability import init_observability
    init_observability()
     
    yield  # Application runs here
    

def create_app() -> FastAPI:
    app = FastAPI(
        title="idapt API",
        lifespan=lifespan
    )
    
    # Configure CORS
    configure_cors(app)
    
    # Mount static files
    #mount_static_files(app)
    
    # Include API router
    from app.api.routers import api_router
    app.include_router(api_router, prefix="/api")
    
    return app

def configure_cors(app: FastAPI):

    from fastapi.middleware.cors import CORSMiddleware

    environment = os.getenv("ENVIRONMENT", "prod")  # Default to 'prod' if not set so that we dont risk exposing the API to the public

    if environment == "dev":
        app.add_middleware(
            CORSMiddleware,
            # For development we allow requests from any origin
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            # For production we only allow requests from the same machine coming from the frontend as traffic is routed through nginx and origin is 127.0.0.1:3000
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

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

    app_host = "0.0.0.0" #os.getenv("HOST_DOMAIN", "0.0.0.0") # For now use 0.0.0.0
    app_port = 8000

    environment = os.getenv("ENVIRONMENT", "prod")  # Default to 'prod' if not set so that we dont risk exposing the API to the public

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
            log_level="info",
            ssl_keyfile="/certs/live/" + os.getenv("HOST_DOMAIN") + "/privkey.pem",
            ssl_certfile="/certs/live/" + os.getenv("HOST_DOMAIN") + "/fullchain.pem"
        )
    else:
        logger.info("Starting in production mode")
        uvicorn.run(
            "main:app",
            host=app_host,
            port=app_port,
            reload=False,
            workers=1,
            log_level="info",
            ssl_keyfile="/certs/live/" + os.getenv("HOST_DOMAIN") + "/privkey.pem",
            ssl_certfile="/certs/live/" + os.getenv("HOST_DOMAIN") + "/fullchain.pem"
        )
