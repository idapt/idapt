from fastapi import Header, Query, HTTPException
from typing import Optional
from app.database.utils.service import get_session
from app.api.user_path import get_user_data_dir
from sqlalchemy.orm import Session
from pathlib import Path
import logging

logger = logging.getLogger("uvicorn")

async def get_user_id(
    x_user_id: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None)
) -> str:
    """Get user ID from header or query parameter"""
    if x_user_id:
        return x_user_id
    if user_id:
        return user_id
    raise HTTPException(status_code=401, detail="User ID is required (either in X-User-Id header or user_id query parameter)") 

# Get a session for the file manager database
def get_file_manager_db_session(user_id: str):
    db_path = get_user_data_dir(user_id) + "/file_manager.db"
    script_location = Path(__file__).parent.parent / "database" / "alembic"
    from app.database.models import Base
    models_declarative_base_class = Base
    with get_session(db_path, str(script_location), models_declarative_base_class) as session:
        # Always initialize default data if needed before yielding the session
        init_default_database_data_if_needed(session, user_id)
        yield session

def init_default_database_data_if_needed(session: Session, user_id: str):
    """
    Initialize default data if needed
    """
    try:
        # Init default settings
        from app.settings.service import init_default_settings_if_needed
        init_default_settings_if_needed(session, user_id)

        # Init default folders
        from app.datasources.file_manager.service.db_operations import create_default_db_filestructure_if_needed
        create_default_db_filestructure_if_needed(session, user_id)

        # Init default datasources
        from app.datasources.service import init_default_datasources_if_needed
        init_default_datasources_if_needed(session)
        
        # Init default processing stacks
        from app.processing_stacks.service import create_default_processing_stacks_if_needed
        create_default_processing_stacks_if_needed(session)
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error initializing default database data: {str(e)}")
        raise
    finally:
        session.close()