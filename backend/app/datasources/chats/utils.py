from app.api.utils import get_user_data_dir
from app.database.utils.service import get_session
from pathlib import Path
import logging
logger = logging.getLogger("uvicorn")


# Get a session for the chat history database
def get_chats_db_session(user_id: str):
    # TODO Implement datasource arg
    db_path = Path(get_user_data_dir(user_id), "chats", "chats.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    script_location = Path(__file__).parent / "database"
    from app.datasources.chats.database.models import Base
    models_declarative_base_class = Base
    with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
        yield session