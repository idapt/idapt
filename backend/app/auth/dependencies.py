from app.auth.service import oauth2_scheme, get_keyring_with_access_sk_token
from app.auth.schemas import Keyring
from app.api.mount_user_data_dir import mount_user_data_dir_dependency
from typing import Annotated, Generator
from fastapi import Depends, HTTPException
import jwt

from app.auth.service import SECRET_KEY, ALGORITHM


import logging
logger = logging.getLogger("uvicorn")

def get_user_uuid_from_token(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """
    Get the user UUID from the token
    """
    try:
        # Decode the token to get the keyring key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Get the keyring key from the payload
        user_uuid: str = payload.get("user_uuid")
        return user_uuid
    except Exception as e:
        logger.error(f"Error getting user UUID from token: {e}")
        raise HTTPException(status_code=500, detail="Error getting user UUID from token")


def get_keyring_with_user_data_mounting_dependency(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)]
) -> Generator[Keyring, None, None]:
    """
    Get the keyring with the token from the auth header
    """
    try:
        # Mount the user data directory
        with mount_user_data_dir_dependency(user_uuid):
            # Get the keyring
            keyring = get_keyring_with_access_sk_token(token)
            yield keyring
    except Exception as e:
        logger.error(f"Error getting keyring with user data mounting dependency: {e}")
        raise HTTPException(status_code=500, detail="Error getting keyring with user data mounting dependency")
