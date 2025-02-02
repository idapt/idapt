
from app.database.utils.service import get_session
from app.api.user_path import get_user_data_dir
from app.datasources.file_manager.service.db_operations import create_default_db_filestructure_if_needed
from sqlalchemy.orm import Session
from pathlib import Path
import logging

logger = logging.getLogger("uvicorn")

# Get a session for the file manager database
def get_file_manager_db_session(user_id: str, datasource_identifier: str):
    db_path = Path(get_user_data_dir(user_id), datasource_identifier, "file_manager.db")
    # Create the parent directories if they don't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    script_location = Path(__file__).parent.parent
    from app.datasources.file_manager.database.models import Base
    models_declarative_base_class = Base
    with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
        # Always initialize default data if needed before yielding the session
        create_default_db_filestructure_if_needed(session, user_id)
        yield session