from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import logging
from pathlib import Path
from sqlalchemy import Connection

logger = logging.getLogger("uvicorn")

def create_alembic_config(script_location: str, connection_string: str) -> Config:
    """Create Alembic config"""
    
    if not Path(script_location).exists():
        raise RuntimeError(f"migrations directory not found at {script_location}")
    
    alembic_cfg = Config()
    # Set the sqlalchemy url as the one in alembic.ini is used for dev
    alembic_cfg.set_main_option('script_location', str(script_location))
    alembic_cfg.set_main_option('sqlalchemy.url', str(connection_string))
    return alembic_cfg

def run_migrations(connection: Connection, connection_string: str, script_location: str, models_declarative_base_class):
    """Run database migrations if needed"""
    try:
        # First check if we need to do any migrations at all
        alembic_cfg = create_alembic_config(script_location, connection_string)
        
        # Check if database needs initialization or migration
        script = ScriptDirectory.from_config(alembic_cfg)
        context = MigrationContext.configure(connection)
        current_heads = context.get_current_heads()
        needs_init = not current_heads
        is_at_latest_revision = set(current_heads) == set(script.get_heads())
        needs_migration = not needs_init and not is_at_latest_revision
        
        # If no migrations needed, return early
        if not needs_init and not needs_migration:
            return    
    
        if needs_init:
            # Database is empty or not initialized
            logger.info(f"Initializing empty database at {connection_string}")
            # Create all tables
            models_declarative_base_class.metadata.create_all(connection)
            logger.info("Database tables created")
            # Stamp with current head
            command.stamp(alembic_cfg, "head")
            logger.info(f"Database initialized and stamped with head revision at {connection_string}")
            
        elif needs_migration:
            logger.info(f"Database not up to date, running migrations at {connection_string}")
            command.upgrade(alembic_cfg, "head")
            logger.info(f"Database migrations completed successfully at {connection_string}")
            
    except Exception as e:
        logger.error(f"Error running database migrations at {connection_string}: {str(e)}")
        raise e