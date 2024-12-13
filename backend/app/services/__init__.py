from typing import Optional
from fastapi import FastAPI
import logging

from app.services.database import DatabaseService
from app.services.generate import GenerateService
from app.services.file_manager import FileManagerService
from app.services.datasource import DatasourceService
from app.services.db_file import DBFileService
from app.services.file import FileService
from app.services.llama_index import LlamaIndexService
from app.services.file_system import FileSystemService
from app.services.ingestion_pipeline import IngestionPipelineService

logger = logging.getLogger(__name__)

class ServiceManager:
    _instance: Optional["ServiceManager"] = None
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services in the correct order"""
        self.logger.info("Initializing services...")
        
        # Core services
        self.db_service = DatabaseService()

        self.db_file_service = DBFileService()
        self.file_system_service = FileSystemService()
        self.file_service = FileService()
        self.llama_index_service = LlamaIndexService()

        # Dependent services
        self.file_manager_service = FileManagerService(self.db_service, self.db_file_service, self.file_system_service, self.llama_index_service)
        
        self.datasource_service = DatasourceService(self.db_service, self.db_file_service, self.file_manager_service)

        self.ingestion_pipeline_service = IngestionPipelineService(self.db_file_service, self.db_service)

        self.generate_service = GenerateService(self.ingestion_pipeline_service)

        self.logger.info("Services initialized successfully")
    
    @classmethod
    def get_instance(cls) -> "ServiceManager":
        if cls._instance is None:
            cls._instance = ServiceManager()
        return cls._instance