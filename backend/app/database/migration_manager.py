from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine
import logging
from pathlib import Path

logger = logging.getLogger("uvicorn")

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
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
        logger.info("Database URL: " + str(engine.url))
        
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
                logger.info("Database tables created")
                # Stamp with current head
                command.stamp(alembic_cfg, "head")
                logger.info("Database initialized and stamped with head revision")

        # If we initialized the database, create default data
        if not current_heads:
            # Create a session for initialization
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Init default datasources
                from app.services.datasource import init_default_datasources
                init_default_datasources(session, logger)
                logger.info("Default datasources initialized")

                # Init default folders
                from app.services.db_file import create_default_db_filestructure
                create_default_db_filestructure(session, logger)
                logger.info("Default folders initialized")
                
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error initializing default data: {str(e)}")
                raise
            finally:
                session.close()
            
            return

        # Check if we need to run migrations
        if not check_current_head(engine):
            logger.info("Database not up to date, running migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        else:
            logger.info("Database is up to date")
            
    except Exception as e:
        logger.error(f"Error running database migrations: {str(e)}")
        raise 