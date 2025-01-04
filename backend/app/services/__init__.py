import logging
from threading import Lock

from app.services.generate import GenerateService
from app.services.file_manager import FileManagerService
from app.services.file import FileService
from app.services.llama_index import LlamaIndexService
from app.services.ollama_status import OllamaStatusService

logger = logging.getLogger(__name__)

class ServiceManager:
    _instance = None
    _lock = Lock()
    _initialized = False
    
    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialize_services()
                    self._initialized = True
    
    def _initialize_services(self):
        """Initialize all services in the correct order"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing services...")
        
        # Initialize stateless services first
        self.ollama_status_service = OllamaStatusService()
        self.ollama_status_service.initialize()

        # Then database-dependent services
        self.file_service = FileService()
        
        self.llama_index_service = LlamaIndexService()
        

        # Dependent services
        self.file_manager_service = FileManagerService(
            self.llama_index_service
        )

        self.generate_service = GenerateService()
        
        self.logger.info("Services initialized successfully")
    
    @classmethod
    def get_instance(cls) -> "ServiceManager":
        if not cls._instance:
            cls._instance = ServiceManager()
        return cls._instance