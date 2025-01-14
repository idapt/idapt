from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine
import logging
from pathlib import Path
from filelock import FileLock
import os

from app.database.connection import get_db_path

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

def run_migrations(engine: Engine, user_id: str):
    """Run database migrations if needed"""
    
    db_folder = Path(get_db_path(user_id)).parent
    
    lock_file = db_folder / "db_init.lock"

    try:
        with FileLock(lock_file, timeout=60):
            alembic_cfg = get_alembic_config(engine)
            
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
                    
                    # Initialize default data
                    from sqlalchemy.orm import sessionmaker
                    Session = sessionmaker(bind=engine)
                    with Session() as session:
                        try:
                            
                            # Init default folders
                            from app.services.db_file import create_default_db_filestructure
                            create_default_db_filestructure(session, user_id)
                            logger.info("Default folders initialized")

                            # Init default datasources
                            from app.services.datasource import init_default_datasources
                            init_default_datasources(session, user_id)
                            logger.info("Default datasources initialized")
                            
                            # Init default processing stacks
                            from app.services.processing_stacks import create_default_processing_stacks
                            create_default_processing_stacks(session)
                            logger.info("Default processing stacks initialized")
                            
                            session.commit()
                        except Exception as e:
                            session.rollback()
                            logger.error(f"Error initializing default data: {str(e)}")
                            raise
                        finally:
                            session.close()
                        
                        return

                        
            if not check_current_head(engine):
                logger.info("Database not up to date, running migrations...")
                command.upgrade(alembic_cfg, "head")
                logger.info("Database migrations completed successfully")
                
    except Exception as e:
        logger.error(f"Error running database migrations: {str(e)}")
        raise
    finally:
        # Cleanup lock file if it exists
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except:
                pass 