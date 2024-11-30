import os
import logging
from sqlalchemy import create_engine, inspect, MetaData
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import time

logger = logging.getLogger(__name__)

# Ignore tables managed by llama index
TABLES_TO_IGNORE = ["data_docstore", "data_embeddings", "data_zettelkasten_docstore", "data_zettelkasten_vectorstore"]

def include_object(object, name, type_, reflected, compare_to):
    """Should you include this table or not?"""
    if type_ == "table" and name in TABLES_TO_IGNORE:
        return False
    return True

class DatabaseMigrationManager:
    def __init__(self, connection_string, max_retries=5, retry_delay=2):
        self.connection_string = connection_string
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.alembic_ini_path = os.path.join(current_dir, "alembic", "alembic.ini")
        
    def _get_alembic_config(self):
        """Get Alembic config with the correct path"""
        if not os.path.exists(self.alembic_ini_path):
            raise FileNotFoundError(f"Alembic config not found at {self.alembic_ini_path}")
        return Config(self.alembic_ini_path)
    
    def run_migrations(self):
        for attempt in range(self.max_retries):
            try:
                engine = create_engine(self.connection_string)
                
                # First check if tables exist
                if not self._tables_exist(engine):
                    logger.info("No tables found. Initializing new database.")
                    self._initialize_new_database(engine)
                    return True
                
                # TODO Fix the fact that the alembic_version table dont get created and so we run this at every backend start.
                # If tables exist, check if migrations are needed
                if self._needs_migration(engine):
                    logger.info("Running pending migrations.")
                    self._run_pending_migrations(engine)
                else:
                    logger.info("Database is up to date, no migrations needed.")
                return True
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Migration attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Failed to run migrations after multiple attempts", exc_info=True)
                    return False
        
    def _needs_migration(self, engine):
        """Check if there are any pending migrations"""
        with engine.connect() as connection:
            # First check if alembic_version table exists
            inspector = inspect(engine)
            if 'alembic_version' not in inspector.get_table_names():
                return True
                
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            # Get the head revision from Alembic
            config = self._get_alembic_config()
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_current_head()
            
            if current_rev != head_rev:
                logger.info(f"Current revision: {current_rev}, Head revision: {head_rev}")
                return True
            return False
                    
    def _tables_exist(self, engine):
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        logger.info(f"Found existing tables: {table_names}")
        return bool(table_names)
        
    def _initialize_new_database(self, engine):
        """Initialize a new database with tables and alembic version"""
        from app.database.models import Base
        
        # Create filtered metadata that excludes data_embeddings and data_docstore
        filtered_metadata = MetaData()
        for table in Base.metadata.tables.values():
            if include_object(table, table.name, "table", False, None):
                table.tometadata(filtered_metadata)
        
        # Create all tables except data_embeddings and data_docstore
        filtered_metadata.create_all(engine)
        
        # Configure alembic and stamp the database
        config = self._get_alembic_config()
        config.set_main_option('sqlalchemy.url', self.connection_string)
        
        # Stamp the alembic version table
        with engine.begin() as connection:
            config.attributes['connection'] = connection
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_current_head()
            command.stamp(config, head_rev)
            
            # Verify the alembic_version table was created
            inspector = inspect(engine)
            if 'alembic_version' not in inspector.get_table_names():
                raise RuntimeError("Failed to create alembic_version table")
        
    def _run_pending_migrations(self, engine):
        """Run any pending migrations"""
        config = self._get_alembic_config()
        config.set_main_option('sqlalchemy.url', self.connection_string)
        
        with engine.connect() as connection:
            config.attributes['connection'] = connection
            from alembic import command
            command.upgrade(config, "head")
