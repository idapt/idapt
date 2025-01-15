from fastapi import BackgroundTasks
import logging
from app.settings.models import AppSettings, OllamaSettings
import httpx
import time
from sqlalchemy.orm import Session
from app.services.settings import get_setting

logger = logging.getLogger("uvicorn")

async def _download_ollama_model(base_url: str, model_name: str):
    """Download a model"""
    if not model_name or not model_name.strip():
        return
        
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Pulling model: {model_name}")
            response = await client.post(
                f"{base_url}/api/pull",
                json={"name": model_name},
                timeout=None
            )
            response.raise_for_status()
            logger.info(f"Successfully pulled model: {model_name}")
        
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {str(e)}")
        raise e
        
async def _check_ollama_model(base_url: str, model_name: str, background_tasks: BackgroundTasks | None = None):
    """Check if a model is installed"""
    if not model_name or not model_name.strip():
        return True
        
    try:
        async with httpx.AsyncClient() as client:
            #logger.info(f"Checking model: {model_name}")
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                installed_models = [model['name'] for model in models_data['models']]
                
                model_name_to_check = f"{model_name}:latest" if ':' not in model_name else model_name
                
                if model_name_to_check not in installed_models and background_tasks:
                    background_tasks.add_task(_download_ollama_model, base_url, model_name)
                    return False
                
                return True
            
    except Exception as e:
        logger.error(f"Error checking/pulling model {model_name}: {str(e)}")
        return False

async def is_ollama_server_reachable(base_url: str) -> bool:
    """Check if the ollama server is reachable"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags")
            return response.status_code == 200
    except Exception as e:
        #logger.error(f"Error checking if ollama server is reachable: {str(e)}")
        return False

# If you dont want to pull the models if not available, set background_tasks to None
async def can_process(session: Session, background_tasks: BackgroundTasks | None = None) -> bool:
    """Check if Ollama models are ready for processing"""
    try:
        # Check if the ollama server is reachable
        app_settings : AppSettings = get_setting(session, "app")
        ollama_settings : OllamaSettings = get_setting(session, "ollama")
        if not await is_ollama_server_reachable(ollama_settings.llm_host):
            # We can't process files if the ollama server is not reachable
            return False

        # Check LLM models
        if app_settings.llm_model_provider == "ollama":
            base_url = ollama_settings.llm_host
            model = ollama_settings.llm_model
            
            if not await _check_ollama_model(base_url, model, background_tasks):
                return False
            
        # Check embedding models
        if app_settings.embedding_model_provider == "ollama":
            base_url = ollama_settings.embedding_host
            model = ollama_settings.embedding_model
            
            if not await _check_ollama_model(base_url, model, background_tasks):
                return False
                
        # If all models are installed or ollama is not used, return True
        return True
    except Exception as e:
        logger.error(f"Error checking if can process: {str(e)}")
        return False 
    
async def wait_for_ollama_models_to_be_downloaded(session: Session):
    """Wait for Ollama models to be ready"""
    while True:
        # Check if we need to wait for Ollama models without pulling them if they don't exist
        if await can_process(session, None):
            return
        
        logger.info("Waiting for Ollama models to be ready before processing files...")
        time.sleep(1)
