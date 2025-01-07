from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_alembic_config() -> Config:
    """Get Alembic config"""
    # Get the directory where alembic.ini is located (project root)
    project_root = Path(__file__).parent.parent.parent
    alembic_ini_path = project_root / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise RuntimeError(f"alembic.ini not found at {alembic_ini_path}")
    
    alembic_cfg = Config(str(alembic_ini_path))
    return alembic_cfg

def check_current_head(engine: Engine) -> bool:
    """Check if database is at the latest revision"""
    alembic_cfg = get_alembic_config()
    script = ScriptDirectory.from_config(alembic_cfg)
    
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        return set(context.get_current_heads()) == set(script.get_heads())

def run_migrations(engine: Engine):
    """Run database migrations if needed"""
    try:
        alembic_cfg = get_alembic_config()
        
        # First check if we need to create/stamp initial database
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_heads = context.get_current_heads()
            
            if not current_heads:
                # Database is empty or not initialized
                logger.info("Initializing empty database...")
                # Create all tables
                from app.database.models import Base
                Base.metadata.create_all(engine)
                
                # Stamp with current head
                command.stamp(alembic_cfg, "head")
                logger.info("Database initialized and stamped with head revision")
                return
        
        # Check if we need to run migrations
        if not check_current_head(engine):
            logger.info("Database not up to date, running migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        else:
            logger.debug("Database is up to date")
            
    except Exception as e:
        logger.error(f"Error running database migrations: {str(e)}")
        raise 