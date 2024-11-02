from functools import lru_cache
import logging
from typing import Optional
from .password_manager import DatabasePasswordManager
from .migration_manager import DatabaseMigrationManager
from app.database.connection import get_connection_string

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    _instance: Optional['DatabaseInitializer'] = None
    _is_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._is_initialized:
            self.password_manager = DatabasePasswordManager()
            self.migration_manager = DatabaseMigrationManager(get_connection_string())
            self._is_initialized = True
    
    def initialize(self):
        """Initialize the database if not already initialized"""
        if not hasattr(self, '_init_complete'):
            logger.info("Starting database initialization")
            self._setup_password()
            self._run_migrations()
            self._init_complete = True
            logger.info("Database initialization completed")
        else:
            logger.debug("Database already initialized, skipping")
    
    def _setup_password(self):
        self.password_manager.ensure_password_file()
    
    def _run_migrations(self):
        self.migration_manager.run_migrations()

@lru_cache()
def get_database_initializer() -> DatabaseInitializer:
    """Get or create the database initializer singleton"""
    return DatabaseInitializer()
