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
    from app.settings.manager import AppSettingsManager
    app_settings = AppSettingsManager.get_instance().settings

    llm_model = None
    llm_base_url = None

    # Pull LLM model first
    if app_settings.llm_model_provider == "custom_ollama":
        llm_base_url = app_settings.custom_ollama.llm_host
        llm_model = app_settings.custom_ollama.llm_model
    else:
        llm_base_url = app_settings.integrated_ollama.llm_host
        llm_model = app_settings.integrated_ollama.llm_model

    _pull_model(llm_base_url, llm_model)

    embedding_model = None
    embedding_base_url = None

    # Then pull embedding model
    if app_settings.embedding_model_provider == "custom_ollama":
        embedding_base_url = app_settings.custom_ollama.embedding_host
        embedding_model = app_settings.custom_ollama.embedding_model
    else:
        embedding_base_url = app_settings.integrated_ollama.embedding_host
        embedding_model = app_settings.integrated_ollama.embedding_model

    _pull_model(embedding_base_url, embedding_model)

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