import threading
import requests
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

def start_ollama_pull_thread():
    threading.Thread(target=pull_ollama_models, daemon=True).start()

def pull_ollama_models():
    """
    Pull Ollama model
    """
    from app.settings.app_settings import AppSettings
    if AppSettings.model_provider == "integrated_ollama":
        base_url = "http://idapt-nginx:3030/integrated-ollama"
        model = AppSettings.ollama_model
        embedding_model = AppSettings.ollama_embedding_model
    else:
        base_url = AppSettings.custom_ollama_host
        model = AppSettings.ollama_model
        embedding_model = AppSettings.ollama_embedding_model

    models_to_pull = [model, embedding_model]
    for model in models_to_pull:
        model = model.strip()
        if not model:
            continue
            
        logger.info("Pulling model: %s", model)
        try:
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model},
                timeout=1200,  # 20 minutes timeout
                stream=True
            )
            response.raise_for_status()

            # Process the response stream
            for line in response.iter_lines():
                if line:
                    try:
                        json.loads(line)  # Parse but don't print
                    except json.JSONDecodeError as e:
                        logger.error("Failed to parse JSON line for model %s: %s", model, str(e))

            logger.info("Successfully pulled model: %s", model)

        except requests.exceptions.RequestException as e:
            logger.error("Failed to pull model %s: %s", model, str(e))