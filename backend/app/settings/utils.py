
from app.database.utils.service import get_session
from app.api.utils import get_user_data_dir
import logging
from pathlib import Path
from app.settings.service import init_default_settings_if_needed

logger = logging.getLogger("uvicorn")

def get_settings_db_session(user_id: str):
    """
    Get a session for the settings database
    """
    db_path = Path(get_user_data_dir(user_id), "settings.db")
    script_location = Path(__file__).parent / "database"
    from app.settings.database.models import Base
    models_declarative_base_class = Base
    with get_session(db_path, str(script_location), models_declarative_base_class) as session:
        # Initialize default settings if they don't exist
        init_default_settings_if_needed(session)
        yield session