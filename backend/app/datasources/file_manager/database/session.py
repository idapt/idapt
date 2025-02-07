
from app.api.db_sessions import get_session_from_cached_database_engine
from app.api.user_path import get_user_data_dir
from app.datasources.file_manager.service.service import initialize_file_manager_db
from app.datasources.database.models import Datasource, DatasourceType
from app.datasources.database.session import get_datasources_db_session
from app.auth.schemas import Keyring
from app.auth.service import get_keyring_with_access_sk_token_from_auth_header

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from pathlib import Path
import logging
from typing import Annotated
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger("uvicorn")

# Get a session for the file manager database
async def get_datasources_file_manager_db_session(
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
        if datasource.type != DatasourceType.FILES.name:
            raise HTTPException(status_code=400, detail="Datasource is not of type files")
        db_path = Path(get_user_data_dir(keyring.user_uuid), datasource.identifier, "file_manager.db")
        # Create the parent directories if they don't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        script_location = Path(__file__).parent
        from app.datasources.file_manager.database.models import Base
        models_declarative_base_class = Base
        async with get_session_from_cached_database_engine(str(db_path), str(script_location), models_declarative_base_class, datasource.dek) as session:
            # Always initialize default data if needed before yielding the session
            initialize_file_manager_db(session, keyring.user_uuid, datasource_name)
            return session
    except Exception as e:
        logger.error(f"Error in get_datasources_file_manager_db_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))