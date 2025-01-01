import logging
import threading
from typing import Set
from fastapi import WebSocket
from app.settings.manager import AppSettingsManager
from app.settings.models import AppSettings
import requests
import json

class OllamaStatusService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections: Set[WebSocket] = set()
        self.is_downloading = False
        self._initialized = False
        self._check_interval = 1  # seconds
        self._stop_event = threading.Event()
        self._check_thread = None
        
    def initialize(self):
        """Safe initialization that can be called after other services"""
        if not self._initialized:
            self._initialized = True
            self.logger.info("OllamaStatusService initialized")
            # Start the background check thread
            self._check_thread = threading.Thread(target=self._check_models_loop, daemon=True)
            self._check_thread.start()
            self.logger.info("OllamaStatusService check thread started")
            
    def _check_models_loop(self):
        """Background thread to periodically check model status"""
        while not self._stop_event.is_set():
            # Set the logger of this thread to the logger passed in and set logging level to info as this is a new thread
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            self._check_and_download_models()
            self._stop_event.wait(self._check_interval)
            
    def _check_and_download_models(self):
        """Check if required models are installed and download if needed"""
        try:

            self.logger.error("Checking models")
            app_settings : AppSettings = AppSettingsManager.get_instance().settings
            
            # Check LLM models
            if app_settings.llm_model_provider == "integrated_ollama":
                self._check_model(
                    app_settings.integrated_ollama.llm_host,
                    app_settings.integrated_ollama.llm_model
                )
            elif app_settings.llm_model_provider == "custom_ollama":
                self._check_model(
                    app_settings.custom_ollama.llm_host,
                    app_settings.custom_ollama.llm_model
                )
                
            # Check embedding models
            if app_settings.embedding_model_provider == "integrated_ollama":
                self._check_model(
                    app_settings.integrated_ollama.embedding_host,
                    app_settings.integrated_ollama.embedding_model
                )
            elif app_settings.embedding_model_provider == "custom_ollama":
                self._check_model(
                    app_settings.custom_ollama.embedding_host,
                    app_settings.custom_ollama.embedding_model
                )
                
        except Exception as e:
            self.logger.error(f"Error checking models: {str(e)}")
            
    def _check_model(self, base_url: str, model_name: str):
        """Check if a model is installed and download if needed"""
        if not model_name or not model_name.strip():
            return
            
        try:
            # Get list of installed models
            response = requests.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                # Extract model names from the response
                installed_models = [model['name'] for model in models_data['models']] if 'models' in models_data else []
                
                if model_name not in installed_models:
                    self.logger.info(f"Model {model_name} not found, starting download...")
                    self.set_status(True)
                    
                    # Pull the model
                    pull_response = requests.post(
                        f"{base_url}/api/pull",
                        json={"name": model_name},
                        stream=True
                    )
                    pull_response.raise_for_status()
                    
                    # Process the stream
                    for line in pull_response.iter_lines():
                        if line:
                            try:
                                json.loads(line)
                            except json.JSONDecodeError:
                                pass  # Skip invalid JSON lines
                                
                    self.logger.info(f"Successfully pulled model: {model_name}")
                    self.set_status(False)
                
        except Exception as e:
            self.logger.error(f"Error checking/pulling model {model_name}: {str(e)}")
            self.set_status(False)
            
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        await websocket.send_json({"is_downloading": self.is_downloading})
        
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast_status(self, is_downloading: bool):
        if self.is_downloading != is_downloading:
            self.is_downloading = is_downloading
            for connection in self.active_connections:
                try:
                    await connection.send_json({"is_downloading": is_downloading})
                except Exception:
                    self.logger.error("Error sending status update to websocket")
                    
    def get_status(self) -> bool:
        return self.is_downloading

    def set_status(self, is_downloading: bool):
        """Synchronously set status and trigger async broadcast"""
        import asyncio
        self.is_downloading = is_downloading
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self.broadcast_status(is_downloading)) 

    def __del__(self):
        """Cleanup when service is destroyed"""
        if self._stop_event:
            self._stop_event.set()
        if self._check_thread and self._check_thread.is_alive():
            self._check_thread.join(timeout=1) 