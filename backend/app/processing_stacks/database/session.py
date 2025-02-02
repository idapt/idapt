from app.database.utils.service import get_session
from app.api.user_path import get_user_data_dir
from app.processing_stacks.service import create_default_processing_stacks_if_needed
from sqlalchemy.orm import Session
from pathlib import Path
import logging

logger = logging.getLogger("uvicorn")

# Get a session for the file manager database
def get_processing_stacks_db_session(user_id: str):
    db_path = Path(get_user_data_dir(user_id), "processing_stacks.db")
    # Create the parent directories if they don't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    script_location = Path(__file__).parent
    from app.processing_stacks.database.models import Base
    models_declarative_base_class = Base
    with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
        # Always initialize default data if needed before yielding the session
        create_default_processing_stacks_if_needed(session)
        yield session