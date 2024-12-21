from functools import lru_cache
import logging
import threading
from typing import Optional
from app.database.initialization.migration_manager import DatabaseMigrationManager
from app.database.connection import get_connection_string

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    _instance: Optional['DatabaseInitializer'] = None
    _is_initialized = False
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._is_initialized:
            with self._lock:
                if not self._is_initialized:
                    self.migration_manager = DatabaseMigrationManager(get_connection_string())
                    self._is_initialized = True
    
    def initialize(self):
        """Initialize the database if not already initialized"""
        with self._lock:
            if not hasattr(self, '_init_complete'):
                logger.info("Starting database initialization")
                self.migration_manager.run_migrations()
                self._init_complete = True
                logger.info("Database initialization completed")
            else:
                logger.debug("Database already initialized, skipping")
    

@lru_cache()
def get_database_initializer() -> DatabaseInitializer:
    """Get or create the database initializer singleton"""
    return DatabaseInitializer()
