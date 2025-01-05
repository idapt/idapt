import asyncio
import logging
from app.settings.manager import AppSettingsManager
from app.settings.models import AppSettings
import requests

logger = logging.getLogger(__name__)
    
async def _download_ollama_model(base_url: str, model_name: str):
    """Download a model"""
    if not model_name or not model_name.strip():
        return
        
    try:
        response = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name},
            stream=True
        )
        response.raise_for_status()
        logger.info(f"Successfully pulled model: {model_name}")
        
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {str(e)}")
        
        
def _check_ollama_model(base_url: str, model_name: str):
    """Check if a model is installed"""
    if not model_name or not model_name.strip():
        return
        
    try:
        # Get list of installed models
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            models_data = response.json()

            # Build the list of installed models names
            installed_models = []
            for model in models_data['models']:
                installed_models.append(model['name'])
                            
            # Normalize model name (add :latest if no tag specified)
            if ':' not in model_name:
                model_name_to_check = f"{model_name}:latest"
            # Otherwise use the original model name given with the tag
            else:
                model_name_to_check = model_name
            
            if model_name_to_check not in installed_models:
                # Trigger model download in background
                asyncio.create_task(_download_ollama_model(base_url, model_name))
                # Return False as the model is not installed
                return False
            
            # If the model is installed, return True
            return True
        
    except Exception as e:
        logger.error(f"Error checking/pulling model {model_name}: {str(e)}")
        return False

def can_process() -> bool:
    """Check if Ollama models are ready for processing"""
    try:
        app_settings : AppSettings = AppSettingsManager.get_instance().settings
        
        # Check LLM models
        if app_settings.llm_model_provider == "ollama":
            base_url = app_settings.ollama.llm_host
            model = app_settings.ollama.llm_model
            
            if not _check_ollama_model(base_url, model):
                return False
            
        # Check embedding models
        if app_settings.embedding_model_provider == "ollama":
            base_url = app_settings.ollama.embedding_host
            model = app_settings.ollama.embedding_model
            
            if not _check_ollama_model(base_url, model):
                return False
                
        # If all models are installed or ollama is not used, return True
        return True
    except Exception as e:
        logger.error(f"Error checking if can process: {str(e)}")
        return False 