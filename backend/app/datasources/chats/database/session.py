from app.api.user_path import get_user_data_dir
from app.auth.service import get_user_uuid_from_token
from app.api.db_sessions import get_session
from app.datasources.database.models import Datasource
from app.datasources.database.session import get_datasources_db_session
from pathlib import Path
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated
import logging
logger = logging.getLogger("uvicorn")


# Get a session for the chat history database
def get_datasources_chats_db_session(
    datasource_name: str,
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    datasources_db_session: Annotated[Session, Depends(get_datasources_db_session)]
):
    datasource = datasources_db_session.query(Datasource).filter(Datasource.name == datasource_name).first()
    db_path = Path(get_user_data_dir(user_uuid), datasource.identifier, "chats.db")
    script_location = Path(__file__).parent
    from app.datasources.chats.database.models import Base
    models_declarative_base_class = Base
    with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
        yield session