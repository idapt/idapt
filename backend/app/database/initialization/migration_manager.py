import os
import logging
from sqlalchemy import create_engine, inspect, MetaData, Engine
from app.database.connection import get_connection_string
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import time

logger = logging.getLogger(__name__)

# Include only the tables from the database model to not affect other tables from the database
TABLES_TO_INCLUDE = ["files", "folders", "datasources", "alembic_version"]
ALEMBIC_INI_PATH = "/backend/app/database/alembic/alembic.ini"
RETRY_DELAY = 2
MAX_RETRIES = 5

def include_object(object, name, type_, reflected, compare_to):
    """Should you include this table or not?"""
    if type_ == "table" and name in TABLES_TO_INCLUDE:
        return True
    return False

def _get_alembic_config():
    """Get Alembic config with the correct path"""
    if not os.path.exists(ALEMBIC_INI_PATH):
        raise FileNotFoundError(f"Alembic config not found at {ALEMBIC_INI_PATH}")
    return Config(ALEMBIC_INI_PATH)

def run_migrations():
    for attempt in range(MAX_RETRIES):
        try:
            # Get the connection string
            connection_string = get_connection_string()
            engine = create_engine(connection_string)
            
            # First check if tables exist
            if not _tables_exist(engine):
                logger.info("No tables found. Initializing new database.")
                _initialize_new_database(engine, connection_string)
                return True
            
            # Check if alembic_version table exists and has a version
            if not _has_alembic_version(engine):
                logger.info("Creating alembic version table and stamping current version.")
                _stamp_alembic_version(engine, connection_string)
                return True
                
            # Only check for migrations if we have a proper version tracking
            if _needs_migration(engine):
                logger.info("Running pending migrations.")
                _run_pending_migrations(engine, connection_string)
            else:
                logger.info("Database is up to date, no migrations needed.")
            return True
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Migration attempt {attempt + 1} failed: {str(e)}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Failed to run migrations after multiple attempts", exc_info=True)
                return False

def _needs_migration(engine: Engine):
    """Check if there are any pending migrations"""
    with engine.connect() as connection:
        # First check if alembic_version table exists
        inspector = inspect(engine)
        if 'alembic_version' not in inspector.get_table_names():
            return True
            
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        
        # Get the head revision from Alembic
        config = _get_alembic_config()
        script = ScriptDirectory.from_config(config)
        head_rev = script.get_current_head()
        
        if current_rev != head_rev:
            logger.info(f"Current revision: {current_rev}, Head revision: {head_rev}")
            return True
        return False
                
def _tables_exist(engine: Engine):
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    logger.info(f"Found existing tables: {table_names}")
    return bool(table_names)
    
def _initialize_new_database(engine: Engine, connection_string: str):
    """Initialize a new database with tables and alembic version"""
    from app.database.models import Base
    
    # Create filtered metadata that excludes data_embeddings and data_docstore
    filtered_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if include_object(table, table.name, "table", False, None):
            table.tometadata(filtered_metadata)
    
    # Create all tables except data_embeddings and data_docstore
    filtered_metadata.create_all(engine)
    
    # Populate default data
    _populate_default_data(engine)
    
    # Configure alembic and stamp the database
    config = _get_alembic_config()
    config.set_main_option('sqlalchemy.url', connection_string)
    
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
    
def _populate_default_data(engine: Engine):
    """Populate the database with default data"""
    
    try:
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            # Initialize default datasources
            from app.services.datasource import _init_default_datasources
            _init_default_datasources(session)

            # Initialize default filestructure
            from app.services.db_file import create_default_db_filestructure
            create_default_db_filestructure(session)

        logger.info("Populated default data")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to populate default data: {str(e)}")
        raise
    finally:
        session.close()

def _run_pending_migrations(engine: Engine, connection_string: str):
    """Run any pending migrations"""
    config = _get_alembic_config()
    config.set_main_option('sqlalchemy.url', connection_string)
    
    with engine.connect() as connection:
        config.attributes['connection'] = connection
        from alembic import command
        command.upgrade(config, "head")

def _has_alembic_version(engine: Engine):
    """Check if alembic_version table exists and has a version"""
    inspector = inspect(engine)
    if 'alembic_version' not in inspector.get_table_names():
        return False
    
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        return current_rev is not None
        
def _stamp_alembic_version(engine: Engine, connection_string: str):
    """Create and stamp the alembic_version table"""
    config = _get_alembic_config()
    config.set_main_option('sqlalchemy.url', connection_string)
    
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.stamp(config, "head")