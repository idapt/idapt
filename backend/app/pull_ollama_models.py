import os
import requests
import yaml
import json

def pull_models():
    config_file_path = os.path.join(os.path.dirname(__file__), '../config/ollama_models.yaml')
    
    if not os.path.exists(config_file_path):
        print("Model configuration file not found.")
        return

    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    models = config.get('models', [])

    for model in models:
        model = model.strip()
        if model:
            print(f"Pulling model: {model}")
            try:
                response = requests.post(
                    "http://" + os.getenv('OLLAMA_HOST') + ":" + os.getenv('OLLAMA_PORT') + "/api/pull",
                    json={"name": model},
                    timeout=1200,  # Increase timeout to 20 minutes
                    stream=True  # Enable streaming
                )
                response.raise_for_status()

                # Process the response as a stream of JSON objects
                for line in response.iter_lines():
                    if line:
                        try:
                            json_line = json.loads(line)
                            print(json_line)
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON line: {e}")

            except requests.exceptions.RequestException as e:
                print(f"Failed to pull model {model}: {e}")