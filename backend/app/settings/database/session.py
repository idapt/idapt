import os
from app.api.db_sessions import get_session
import logging
from pathlib import Path
from app.settings.service import init_default_settings_if_needed
from app.auth.schemas import Keyring
from fastapi import Depends, HTTPException
from typing import Annotated
from app.auth.dependencies import get_keyring_with_user_data_mounting_dependency
from app.api.fernet_stored_encryption_key import FernetStoredEncryptionKey
from app.api.aes_gcm_file_encryption import generate_aes_gcm_key
from sqlalchemy.orm import Session

logger = logging.getLogger("uvicorn")

SETTINGS_DB_PATH = "/data/{user_uuid}/settings/settings.db"
SETTINGS_DEK_PATH = "/data/{user_uuid}/settings/settings_dek.txt"

def get_settings_db_session(keyring : Annotated[Keyring, Depends(get_keyring_with_user_data_mounting_dependency)]) -> Session:
    """
    Get a session for the settings database
    The session is cached for 30 seconds to avoid re-reading and decrypting the database file from the disk and reuse the same session
    """
    try:
        
        db_path = SETTINGS_DB_PATH.format(user_uuid=keyring.user_uuid)
        script_location = Path(__file__).parent
        from app.settings.database.models import Base
        models_declarative_base_class = Base

        # If the key file does not exist, create it
        if not os.path.exists(SETTINGS_DEK_PATH.format(user_uuid=keyring.user_uuid)):
            # Create required directories
            os.makedirs(os.path.dirname(SETTINGS_DEK_PATH.format(user_uuid=keyring.user_uuid)), exist_ok=True)
            # Create the key AES-GCM 128 bits dek for the settings database
            settings_dek = generate_aes_gcm_key()
            FernetStoredEncryptionKey.store_encrypted_key_at_path(
                key=settings_dek,
                kek=keyring.kek_settings,
                stored_key_path=SETTINGS_DEK_PATH.format(user_uuid=keyring.user_uuid)
            )
        # Decrypt the settings encryption key from the stored file with the settings kek
        settings_dek = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=SETTINGS_DEK_PATH.format(user_uuid=keyring.user_uuid),
            kek=keyring.kek_settings
        )

        # Get the session from the cached database engine
        with get_session(str(db_path), str(script_location), models_declarative_base_class) as settings_db_session:
            try:
                # Initialize default settings if they don't exist
                init_default_settings_if_needed(settings_db_session=settings_db_session)

                return settings_db_session

            except Exception as e:
                logger.error(f"Error getting settings database session: {e}")
                raise HTTPException(status_code=500, detail="Error getting settings database session")
    except Exception as e:
        logger.error(f"Error getting settings database session: {e}")
        raise HTTPException(status_code=500, detail="Error getting settings database session")
