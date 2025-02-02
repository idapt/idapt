from app.api.user_path import get_user_data_dir
from app.database.utils.service import get_session
from pathlib import Path
import logging
logger = logging.getLogger("uvicorn")


# Get a session for the chat history database
def get_datasources_chats_db_session(user_id: str, datasource_identifier: str):
    db_path = Path(get_user_data_dir(user_id), datasource_identifier, "chats.db")
    script_location = Path(__file__).parent / "database"
    from app.datasources.chats.database.models import Base
    models_declarative_base_class = Base
    with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
        yield session