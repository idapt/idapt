import os
import requests
import yaml
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def pull_models():
    """
    Pull Ollama models from config. Using lru_cache to ensure this only runs once.
    """
    config_file_path = os.path.join(os.path.dirname(__file__), '../config/ollama_models.yaml')
    
    if not os.path.exists(config_file_path):
        logger.error("Model configuration file not found at: %s", config_file_path)
        return
    
    try:
        with open(config_file_path, 'r') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        logger.error("Failed to load model configuration: %s", str(e))
        return

    models = config.get('models', [])
    if not models:
        logger.warning("No models configured in %s", config_file_path)
        return

    ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
    ollama_port = os.getenv('OLLAMA_PORT', '11434')
    base_url = f"http://{ollama_host}:{ollama_port}"

    for model in models:
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