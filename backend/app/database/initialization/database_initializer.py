from functools import lru_cache
import logging
import threading
from typing import Optional
from app.database.initialization.password_manager import DatabasePasswordManager
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
                    self.password_manager = DatabasePasswordManager()
                    self.migration_manager = DatabaseMigrationManager(get_connection_string())
                    self._is_initialized = True
    
    def initialize(self):
        """Initialize the database if not already initialized"""
        with self._lock:
            if not hasattr(self, '_init_complete'):
                logger.info("Starting database initialization")
                self._setup_password()
                self._run_migrations()
                self._init_complete = True
                logger.info("Database initialization completed")
            else:
                logger.debug("Database already initialized, skipping")
    
    def _setup_password(self):
        # Ensure the password file path exists
        self.password_manager.ensure_password_file()
        # Generate a password if not already set
        if not self.password_manager.read_stored_password():
            password = self.password_manager.generate_password()
            self.password_manager.write_password(password)
            logger.info("Generated and stored a new database password")

            # Update the database password
            self.password_manager.update_database_password(password)
        else:
            logger.info("Database password already set")

    def _run_migrations(self):
        self.migration_manager.run_migrations()

@lru_cache()
def get_database_initializer() -> DatabaseInitializer:
    """Get or create the database initializer singleton"""
    return DatabaseInitializer()
