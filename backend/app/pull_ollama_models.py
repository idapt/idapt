import threading
import requests
import json
import logging

logger = logging.getLogger(__name__)

def start_ollama_pull_thread():
    """Start a single thread for pulling both LLM and embedding models"""
    threading.Thread(target=pull_ollama_models, daemon=True).start()

def pull_ollama_models():
    """Pull both Ollama LLM and embedding models sequentially"""
    from app.settings.app_settings import AppSettings
    
    # Pull LLM model first
    if AppSettings.model_provider == "custom_ollama":
        base_url = AppSettings.custom_ollama_llm_host
    else:
        base_url = AppSettings.integrated_ollama_llm_host
    model = AppSettings.ollama_model
    _pull_model(base_url, model)

    # Then pull embedding model
    if AppSettings.embedding_model_provider == "custom_ollama":
        base_url = AppSettings.custom_ollama_embedding_host
    else:
        base_url = AppSettings.integrated_ollama_embedding_host
    model = AppSettings.ollama_embedding_model
    _pull_model(base_url, model)

def _pull_model(base_url: str, model: str):
    """Helper function to pull a model from Ollama"""
    if not model or not model.strip():
        return

    logger.info("Pulling model: %s from %s", model, base_url)
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