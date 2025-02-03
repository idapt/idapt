from fastapi import Depends
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Annotated

from app.datasources.service import init_default_datasources_if_needed
from app.settings.database.session import get_settings_db_session
from app.database.utils.service import get_session
from app.api.user_path import get_user_data_dir
from app.api.utils import get_user_id

logger = logging.getLogger("uvicorn")

def get_datasources_db_session(
    user_id: Annotated[str, Depends(get_user_id)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)]
):
    """
    Get a session for the datasources database
    """
    db_path = Path(get_user_data_dir(user_id), "datasources.db")
    script_location = Path(__file__).parent
    from app.datasources.database.models import Base
    models_declarative_base_class = Base
    with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
        # Initialize default datasources if they don't exist
        init_default_datasources_if_needed(
            datasources_db_session=session, 
            settings_db_session=settings_db_session,
            user_id=user_id
        )
        # Settings session is closed here

        yield session