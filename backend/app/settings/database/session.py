
from app.database.utils.service import get_encrypted_database_session
from app.api.user_path import get_user_data_dir
import logging
from pathlib import Path
from app.settings.service import init_default_settings_if_needed
from app.auth.schemas import Keyring
from fastapi import Depends
from typing import Annotated
from app.auth.service import get_keyring_with_token

logger = logging.getLogger("uvicorn")

def get_settings_db_session(keyring: Annotated[Keyring, Depends(get_keyring_with_token)]):
    """
    Get a session for the settings database
    """
    db_path = Path(get_user_data_dir(keyring.user_uuid), "settings.db")
    script_location = Path(__file__).parent
    from app.settings.database.models import Base
    models_declarative_base_class = Base
    with get_encrypted_database_session(str(db_path), str(script_location), models_declarative_base_class, keyring.settings_encryption_key) as session:
        # Initialize default settings if they don't exist
        init_default_settings_if_needed(settings_db_session=session)
        yield session