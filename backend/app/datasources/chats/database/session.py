from app.api.user_path import get_user_data_dir
from app.auth.service import get_user_uuid_from_token
from app.api.db_sessions import get_session_from_cached_database_engine
from app.datasources.database.models import Datasource, DatasourceType
from app.datasources.database.session import get_datasources_db_session
from app.auth.schemas import Keyring
from app.auth.service import get_keyring_with_access_sk_token_from_auth_header
from pathlib import Path
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Annotated
import logging
logger = logging.getLogger("uvicorn")


# Get a session for the chat history database
async def get_datasources_chats_db_session(
    datasource_name: str,
    keyring : Annotated[Keyring, Depends(get_keyring_with_access_sk_token_from_auth_header)],
    datasources_db_session: Annotated[Session, Depends(get_datasources_db_session)]
) -> Session:
    """
    Get a session for the file manager database
    """
    try:
        datasource = datasources_db_session.query(Datasource).filter(Datasource.name == datasource_name).first()
        if not datasource:
            raise HTTPException(status_code=400, detail="Datasource not found")
        if datasource.type != DatasourceType.CHATS.name:
            raise HTTPException(status_code=400, detail="Datasource is not of type chats")
        db_path = Path(get_user_data_dir(keyring.user_uuid), datasource.identifier, "chats.db")
        # Create the parent directories if they don't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        script_location = Path(__file__).parent
        from app.datasources.chats.database.models import Base
        models_declarative_base_class = Base
        async with get_session_from_cached_database_engine(str(db_path), str(script_location), models_declarative_base_class, datasource.dek) as session:
            return session
    except Exception as e:
        logger.error(f"Error in get_datasources_file_manager_db_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))