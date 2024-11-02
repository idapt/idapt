import logging
from functools import lru_cache
from .password_manager import DatabasePasswordManager
from .migration_manager import DatabaseMigrationManager
from app.database.connection import get_connection_string

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.password_manager = DatabasePasswordManager()
            self.migration_manager = DatabaseMigrationManager(get_connection_string())
            self._initialized = True
    
    def initialize(self):
        if not hasattr(self, '_init_complete'):
            logger.info("Starting database initialization")
            self._setup_password()
            self._run_migrations()
            self._init_complete = True
        else:
            logger.debug("Database already initialized, skipping")
    
    def _setup_password(self):
        self.password_manager.ensure_password_file()
        stored_password = self.password_manager.read_stored_password()
        
        if not stored_password:
            new_password = self.password_manager.generate_password()
            self.password_manager.write_password(new_password)
            self.password_manager.update_database_password(new_password)
            
    def _run_migrations(self):
        self.migration_manager.run_migrations()

def initialize_database():
    """Initialize database (singleton instance)"""
    initializer = DatabaseInitializer()
    initializer.initialize()
