import os
import requests
import yaml
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

def pull_ollama_models(models: list[str]):
    """
    Pull Ollama model
    """
    
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