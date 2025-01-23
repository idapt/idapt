from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine
import logging
from pathlib import Path
from filelock import FileLock
import os

logger = logging.getLogger("uvicorn")

def get_alembic_config(engine: Engine) -> Config:
    """Get Alembic config"""
    script_location = Path(__file__).parent / "alembic"
    
    if not script_location.exists():
        raise RuntimeError(f"migrations directory not found at {script_location}")
    
    alembic_cfg = Config()
    # Set the sqlalchemy url as the one in alembic.ini is used for dev
    alembic_cfg.set_main_option('script_location', str(script_location))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
    return alembic_cfg

def check_current_head(engine: Engine) -> bool:
    """Check if database is at the latest revision"""
    alembic_cfg = get_alembic_config(engine)
    script = ScriptDirectory.from_config(alembic_cfg)
    
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        return set(context.get_current_heads()) == set(script.get_heads())

def run_migrations(engine: Engine, db_path: str):
    """Run database migrations if needed"""
    lock_file = None  # Initialize lock_file variable
    try:
        # First check if we need to do any migrations at all
        alembic_cfg = get_alembic_config(engine)
        
        # Check if database needs initialization or migration
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_heads = context.get_current_heads()
            needs_init = not current_heads
            needs_migration = not needs_init and not check_current_head(engine)
            
            # If no migrations needed, return early
            if not needs_init and not needs_migration:
                return
                
        # Only create lock file and use FileLock if we actually need to perform migrations
        db_folder = Path(db_path).parent
        if not db_folder.exists():
            db_folder.mkdir(parents=True, exist_ok=True)
            
        lock_file = db_folder / "db_init.lock"
        
        # Create the lock file if it doesn't exist
        lock_file.touch(exist_ok=True)
        
        with FileLock(lock_file, timeout=60):
            if needs_init:
                # Database is empty or not initialized
                logger.info("Initializing empty database...")
                # Create all tables
                from app.database.models import Base
                Base.metadata.create_all(engine)
                logger.info("Database tables created")
                # Stamp with current head
                command.stamp(alembic_cfg, "head")
                logger.info("Database initialized and stamped with head revision")
            
            elif needs_migration:
                logger.info("Database not up to date, running migrations...")
                command.upgrade(alembic_cfg, "head")
                logger.info("Database migrations completed successfully")
                
    except Exception as e:
        logger.error(f"Error running database migrations: {str(e)}")
        raise
    finally:
        # Only try to remove the lock file if it was created
        if lock_file is not None and os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception as e:
                logger.error(f"Error removing lock file: {str(e)}")
                pass 