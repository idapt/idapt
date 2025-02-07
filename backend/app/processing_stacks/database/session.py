from app.api.db_sessions import get_session_from_cached_database_engine
from app.processing_stacks.service import create_default_processing_stacks_if_needed
from sqlalchemy.orm import Session
from pathlib import Path
import os
import logging
from app.auth.schemas import Keyring
from fastapi import Depends, HTTPException
from app.auth.service import get_keyring_with_access_sk_token_from_auth_header
from app.api.fernet_stored_encryption_key import FernetStoredEncryptionKey
from typing import Annotated
from app.api.aes_gcm_file_encryption import generate_aes_gcm_key
from typing import Generator

logger = logging.getLogger("uvicorn")

PROCESSING_STACKS_DB_PATH = "/data/{user_uuid}/processing_stacks/processing_stacks.db"
PROCESSING_STACKS_DEK_PATH = "/data/{user_uuid}/processing_stacks/processing_stacks_dek.txt"

async def get_processing_stacks_db_session(
    keyring : Annotated[Keyring, Depends(get_keyring_with_access_sk_token_from_auth_header)]
) -> Generator[Session, None, None]:
    """
    Get a session for the processing stacks database
    """
    try:
        db_path = PROCESSING_STACKS_DB_PATH.format(user_uuid=keyring.user_uuid)
        script_location = Path(__file__).parent
        from app.processing_stacks.database.models import Base
        models_declarative_base_class = Base
        
        # If the key do not exist, create it
        if not os.path.exists(PROCESSING_STACKS_DEK_PATH.format(user_uuid=keyring.user_uuid)):
            # Create required directories
            os.makedirs(os.path.dirname(PROCESSING_STACKS_DEK_PATH.format(user_uuid=keyring.user_uuid)), exist_ok=True)
            # Create the key AES-GCM 128 bits dek for the processing stacks database
            processing_stacks_dek = generate_aes_gcm_key()
            FernetStoredEncryptionKey.store_encrypted_key_at_path(
                key=processing_stacks_dek,
                kek=keyring.kek_processing_stacks,
                stored_key_path=PROCESSING_STACKS_DEK_PATH.format(user_uuid=keyring.user_uuid)
            )
        # Decrypt the processing stacks encryption key from the stored file with the processing stacks kek
        processing_stacks_dek = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=PROCESSING_STACKS_DEK_PATH.format(user_uuid=keyring.user_uuid),
            kek=keyring.kek_processing_stacks
        )

        async with get_session_from_cached_database_engine(
            db_path=str(db_path),
            script_location=str(script_location),
            models_declarative_base_class=models_declarative_base_class,
            dek=processing_stacks_dek
        ) as processing_stacks_db_session:
            try:
                # Initialize default settings if they don't exist
                create_default_processing_stacks_if_needed(processing_stacks_db_session=processing_stacks_db_session)

                return processing_stacks_db_session

            except Exception as e:
                logger.error(f"Error getting processing stacks database session: {e}")
                raise HTTPException(status_code=500, detail="Error getting processing stacks database session")
    except Exception as e:
        logger.error(f"Error getting processing stacks database session: {e}")
        raise HTTPException(status_code=500, detail="Error getting processing stacks database session")
