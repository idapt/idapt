import json
from fastapi import BackgroundTasks
import logging
from app.settings.schemas import AppSettings, OllamaLLMSettings, OllamaEmbedSettings
import httpx
import time
from sqlalchemy.orm import Session
from app.settings.service import get_setting
from app.datasources.models import Datasource

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
        
async def _check_ollama_model(base_url: str, model_name: str):
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
                
                if model_name_to_check not in installed_models:
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
async def can_process(session: Session, download_models: bool = True) -> bool:
    """Check if Ollama models are ready for processing"""
    try:
        # TODO Also check for other models
        # Get all datasources
        datasources = session.query(Datasource).all()
        # Check if any datasource is using ollama
        for datasource in datasources:
            if datasource.embedding_provider == "ollama_embed":
                ollama_embed_settings : OllamaEmbedSettings = OllamaEmbedSettings(**json.loads(datasource.embedding_settings))
                # Check if the ollama server is reachable
                if not await is_ollama_server_reachable(ollama_embed_settings.host):
                    # We can't process files if the ollama server is not reachable, skip this processing request
                    #logger.error("Ollama server is not reachable, skipping processing request")
                    return False
                if not await _check_ollama_model(ollama_embed_settings.host, ollama_embed_settings.model):
                    logger.info(f"Model {ollama_embed_settings.model} not found, downloading...")
                    if download_models:
                        await _download_ollama_model(ollama_embed_settings.host, ollama_embed_settings.model)
                        # Check again if the model is installed
                        if not await _check_ollama_model(ollama_embed_settings.host, ollama_embed_settings.model):
                            logger.error(f"Model {ollama_embed_settings.model} still not found after downloading")
                            return False
                    else:
                        return False
                    
        # Check llm model
        app_settings : AppSettings = get_setting(session, "app")
        if app_settings.llm_model_provider == "ollama_llm":
            ollama_llm_settings : OllamaLLMSettings = get_setting(session, "ollama_llm")
            # Check if the ollama server is reachable
            if not await is_ollama_server_reachable(ollama_llm_settings.host):
                # We can't process files if the ollama server is not reachable, skip this processing request
                logger.error("Ollama server is not reachable, skipping processing request")
                return False
            if not await _check_ollama_model(ollama_llm_settings.host, ollama_llm_settings.model):
                logger.info(f"Model {ollama_llm_settings.model} not found, downloading...")
                if download_models:
                    await _download_ollama_model(ollama_llm_settings.host, ollama_llm_settings.model)
                    # Check again if the model is installed
                    if not await _check_ollama_model(ollama_llm_settings.host, ollama_llm_settings.model):
                        logger.error(f"Model {ollama_llm_settings.model} still not found after downloading")
                        return False
                else:
                    return False
        
        # If all models are installed or ollama is not used, return True
        return True
    except Exception as e:
        logger.error(f"Error checking if can process: {str(e)}")
        return False 
    
async def trigger_download_and_wait_for_ollama_models_to_be_downloaded(session: Session):
    """Wait for Ollama models to be ready"""
    while True:
        # Check if we need to wait for Ollama models without pulling them if they don't exist
        if await can_process(session):
            return
        
        logger.info("Waiting for Ollama models to be ready before processing files...")
        time.sleep(1)