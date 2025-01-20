from fastapi import FastAPI

def configure_cors(app: FastAPI, environment: str):

    from fastapi.middleware.cors import CORSMiddleware

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