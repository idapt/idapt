from fastapi import Depends, HTTPException
import logging
from pathlib import Path
from sqlalchemy.orm import Session
import os
from typing import Annotated, Generator

from app.datasources.service import init_default_datasources_if_needed
from app.settings.database.session import get_settings_db_session
from app.api.db_sessions import get_session
from app.api.aes_gcm_file_encryption import generate_aes_gcm_key
from app.auth.schemas import Keyring
from app.auth.dependencies import get_keyring_with_user_data_mounting_dependency
from app.api.fernet_stored_encryption_key import FernetStoredEncryptionKey

logger = logging.getLogger("uvicorn")        

DATASOURCES_DB_PATH = "/data/{user_uuid}/datasources/datasources.db"
DATASOURCES_DEK_PATH = "/data/{user_uuid}/datasources/datasources_dek.txt"

def get_datasources_db_session(
    keyring : Annotated[Keyring, Depends(get_keyring_with_user_data_mounting_dependency)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)]
) -> Session:
    """
    Get a session for the datasources database
    """
    try:
        db_path = DATASOURCES_DB_PATH.format(user_uuid=keyring.user_uuid)
        script_location = Path(__file__).parent
        from app.datasources.database.models import Base
        models_declarative_base_class = Base

        # If the key do not exist, create it
        if not os.path.exists(DATASOURCES_DEK_PATH.format(user_uuid=keyring.user_uuid)):
            # Create required directories
            os.makedirs(os.path.dirname(DATASOURCES_DEK_PATH.format(user_uuid=keyring.user_uuid)), exist_ok=True)
            # Create the key AES-GCM 128 bits dek for the datasources database
            datasources_dek = generate_aes_gcm_key()
            FernetStoredEncryptionKey.store_encrypted_key_at_path(
                key=datasources_dek,
                kek=keyring.kek_datasources,
                stored_key_path=DATASOURCES_DEK_PATH.format(user_uuid=keyring.user_uuid)
            )
        # Decrypt the datasources encryption key from the stored file with the datasources kek
        datasources_dek = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=DATASOURCES_DEK_PATH.format(user_uuid=keyring.user_uuid),
            kek=keyring.kek_datasources
        )

        with get_session(
            db_path=str(db_path),
            script_location=str(script_location),
            models_declarative_base_class=models_declarative_base_class
        ) as datasources_db_session:
            try:
                # Initialize default datasources if they don't exist
                init_default_datasources_if_needed(
                    datasources_db_session=datasources_db_session, 
                    settings_db_session=settings_db_session,
                    user_uuid=keyring.user_uuid
                )

                return datasources_db_session

            except Exception as e:
                logger.error(f"Error getting datasources database session: {e}")
                raise HTTPException(status_code=500, detail="Error getting datasources database session")
    except Exception as e:
        logger.error(f"Error getting datasources database session: {e}")
        raise HTTPException(status_code=500, detail="Error getting datasources database session")
