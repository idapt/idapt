from app.auth.schemas import TokenData, Keyring
from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from cryptography.fernet import Fernet
import logging
from app.api.user_path import get_user_data_dir
from pathlib import Path
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("uvicorn")

fernet_key = Fernet.generate_key()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/auth/token",
    #scopes={
    #    "datasources": "Datasources decryption key", # TODO Add a per datasource decryption key
    #    "processing": "Processing decryption key",
    #    "processing_stacks": "Processing stacks decryption key",
    #    "settings": "Settings decryption key",
    #}
)

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60 # 30 days

KEYRING_PATH = "keyring.json"
KEYRING_KEY_PATH = "keyring_key.json"

def decrypt_keyring(user_uuid: str, keyring_key: str) -> Keyring:
    """
    Decrypts the keyring from the keyring file using the keyring key provided.
    """
    try:
        keyring_fernet = Fernet(keyring_key)
        with open(str(Path(get_user_data_dir(user_uuid)) / KEYRING_PATH), "rb") as f:
            keyring_value = keyring_fernet.decrypt(f.read())
            try:
                keyring = Keyring.model_validate_json(keyring_value)
                return keyring
            except Exception as e:
                logger.error(f"Error decrypting keyring, wrong keyring key: {e}")
                raise HTTPException(status_code=500, detail="Error decrypting keyring, wrong keyring key")
    except Exception as e:
        logger.error(f"Error decrypting keyring: {e}")
        raise HTTPException(status_code=500, detail="Error decrypting keyring")


def encrypt_keyring(user_uuid: str, keyring: Keyring, keyring_key: str):
    """
    Encrypts the keyring and saves it to the keyring file using the keyring key provided.
    """
    try:
        keyring_fernet = Fernet(keyring_key)
        keyring_json = keyring.model_dump_json()
        encrypted_keyring = keyring_fernet.encrypt(keyring_json.encode("utf-8")).decode("utf-8")
        with open(str(Path(get_user_data_dir(user_uuid)) / KEYRING_PATH), "wb") as f:
            f.write(encrypted_keyring.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error encrypting keyring: {e}")
        raise HTTPException(status_code=500, detail="Error encrypting keyring")


def create_keyring_key():
    """
    Creates a new keyring encryption key.
    """
    try:
        return Fernet.generate_key().decode("utf-8")
    except Exception as e:
        logger.error(f"Error creating keyring key: {e}")
        raise HTTPException(status_code=500, detail="Error creating keyring key")

def decrypt_stored_keyring_key(user_uuid: str, master_password_fernet_key: str) -> str:
    """
    Decrypts the stored keyring encryption key.
    """
    try:
        master_password_fernet_key_fernet = Fernet(master_password_fernet_key)
        with open(str(Path(get_user_data_dir(user_uuid)) / KEYRING_KEY_PATH), "rb") as f:
            keyring_key : str = master_password_fernet_key_fernet.decrypt(f.read()).decode("utf-8")
        return keyring_key
    except Exception as e:
        logger.error(f"Error decrypting stored keyring key: {e}")
        raise HTTPException(status_code=500, detail="Error decrypting stored keyring key")

def get_fernet_key_from_password(password: str) -> bytes:
    """Convert a password into a valid Fernet key"""
    # Use PBKDF2 to derive a 32-byte key from the password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'static_salt',  # You might want to use a per-user salt
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_and_store_keyring_key(user_uuid: str, keyring_key: str, master_password_fernet_key: str):
    """
    Encrypts the keyring encryption key and saves it to the keyring key file.
    """
    try:
        # Convert master password to a valid Fernet key
        master_password_fernet_key_fernet = Fernet(master_password_fernet_key)
        
        keyring_key_encrypted = master_password_fernet_key_fernet.encrypt(keyring_key.encode("utf-8")).decode("utf-8")
        with open(str(Path(get_user_data_dir(user_uuid)) / KEYRING_KEY_PATH), "wb") as f:
            f.write(keyring_key_encrypted.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error encrypting and storing keyring key: {e}")
        raise HTTPException(status_code=500, detail="Error encrypting and storing keyring key")

def create_jwt_access_token(data: dict, expires_delta: timedelta):
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT access token: {e}")
        raise HTTPException(status_code=500, detail="Error creating JWT access token")

def get_token_with_password(user_uuid: str, master_password: str) -> TokenData:
    try:
        # Convert master password to a valid Fernet key
        master_password_fernet_key = get_fernet_key_from_password(master_password)
        
        # Get the paths to the keyring and keyring key files for the user
        user_keyring_path = str(Path(get_user_data_dir(user_uuid)) / KEYRING_PATH)

        # Check if the keyring file exists
        if not os.path.exists(user_keyring_path):
            # If it doesn't exist, initialize a new keyring
            new_keyring_key = init_new_keyring(user_uuid, master_password_fernet_key)
        else:
            # If it exists, decrypt the keyring key using the master password
            old_keyring_key = decrypt_stored_keyring_key(user_uuid, master_password_fernet_key)

            # Decrypt the keyring using the keyring key
            keyring = decrypt_keyring(user_uuid, old_keyring_key)

            # Rotate the keyring key
            new_keyring_key = rotate_keyring_key(user_uuid, keyring, master_password_fernet_key)

        # Create the token data and send the current keyring key to the user
        token_data = TokenData(
            user_uuid=user_uuid,
            keyring_key=new_keyring_key
        )
        return token_data
    except Exception as e:
        logger.error(f"Error getting keyring: {e}")
        raise HTTPException(status_code=500, detail="Error getting keyring")

def rotate_keyring_key(user_uuid: str, keyring: Keyring, master_password_fernet_key: str) -> str:
    """
    Rotates the keyring key safely and returns the new keyring key.
    """
    try:
        # Get the paths to the keyring and keyring key files for the user
        user_keyring_path = str(Path(get_user_data_dir(user_uuid)) / KEYRING_PATH)
        user_keyring_key_path = str(Path(get_user_data_dir(user_uuid)) / KEYRING_KEY_PATH)

        # Create a new keyring key to rotate it
        new_keyring_key = create_keyring_key()

        # Move the old encrypted keyring file to another file for recovery in case of failure
        os.rename(user_keyring_path, user_keyring_path + ".old")

        # Encrypt the keyring using the new keyring key into a new .new file
        encrypt_keyring(user_uuid, keyring, new_keyring_key)

        # Move the old keyring key file to another file for recovery in case of failure
        os.rename(user_keyring_key_path, user_keyring_key_path + ".old")

        # Encrypt the keyring key and store it so that if the user looses it he can use the master password to rotate it and get a new one
        # This will overwrite the old keyring key file
        encrypt_and_store_keyring_key(user_uuid, new_keyring_key, master_password_fernet_key)

        # Try to decrypt the keyring key file to be sure that everything is ok and no data is corrupted
        stored_new_keyring_key = decrypt_stored_keyring_key(user_uuid, master_password_fernet_key)
        if stored_new_keyring_key != new_keyring_key:
            raise HTTPException(status_code=500, detail="Error encrypting and storing keyring key, keeping the old one. This should never happen.")

        # Try to decrypt the keyring using the new keyring key to be sure that everything is ok and no data is corrupted
        # This will raise if the keyring is not validated by pydantic and the decryption failed
        _ = decrypt_keyring(user_uuid, stored_new_keyring_key)

        # Everything is working as expected, delete the old files

        # Delete the old keyring file
        os.remove(user_keyring_path + ".old")

        # Delete the old keyring key file
        os.remove(user_keyring_key_path + ".old")

        # Return the new keyring key
        return new_keyring_key
    except Exception as e:
        # If something goes wrong, restore the old files so that we can still decrypt the keyring with the old keyring key with the master password
        # TODO Implement recovery codes given to the user and add other keyring keys encrypted with them so that if the user loose access to his master_password he can still recover his data using these.
        if os.path.exists(user_keyring_path + ".old"):
            os.rename(user_keyring_path + ".old", user_keyring_path)
        if os.path.exists(user_keyring_key_path + ".old"):
            os.rename(user_keyring_key_path + ".old", user_keyring_key_path)
        return None


def get_keyring_with_token(token: Annotated[str, Depends(oauth2_scheme)]) -> Keyring:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        try:
            # Decode the token to get the keyring key
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Get the keyring key from the payload
            user_uuid: str = payload.get("sub")
            keyring_key: str = payload.get("keyring_key")
            if user_uuid is None or keyring_key is None:
                raise credentials_exception
            # Recreate the token data
            token_data = TokenData(user_uuid=user_uuid, keyring_key=keyring_key)
        except InvalidTokenError:
            raise credentials_exception
        # Decrypt the keyring using the keyring key
        keyring = decrypt_keyring(token_data.user_uuid, token_data.keyring_key)
        if keyring is None:
            raise credentials_exception
        # Return the keyring
        return keyring
    except Exception as e:
        logger.error(f"Error getting keyring: {e}")
        raise credentials_exception

def init_new_keyring(user_uuid: str, master_password_fernet_key: str) -> str:
    """
    Initializes a new keyring for a user and returns the keyring key.
    """
    try:
        # Get the path to the keyring file for the user
        user_keyring_path = str(Path(get_user_data_dir(user_uuid)) / KEYRING_PATH)

        # Check if the keyring file exists
        if os.path.exists(user_keyring_path) or os.path.exists(user_keyring_path + ".old"):
            raise HTTPException(status_code=400, detail="Keyring already exists")
        
        # Create the keyring directory if needed
        #os.makedirs(user_keyring_path.parent, exist_ok=True)

        # Create a new keyring key
        keyring_key = create_keyring_key()
        # Create a new keyring with new random keys for each service
        keyring = Keyring(
            user_uuid=user_uuid,
            datasources_encryption_key=Fernet.generate_key().decode("utf-8"),
            processing_encryption_key=Fernet.generate_key().decode("utf-8"),
            processing_stacks_encryption_key=Fernet.generate_key().decode("utf-8"),
            settings_encryption_key=Fernet.generate_key().decode("utf-8")
        )
        # Encrypt the keyring key and store it so that if the user looses it he can use the master password to rotate it and get a new one
        encrypt_and_store_keyring_key(user_uuid, keyring_key, master_password_fernet_key)
        # Encrypt the keyring and save it to the keyring file
        encrypt_keyring(user_uuid, keyring, keyring_key)
        # Validate the keyring key file
        stored_keyring_key = decrypt_stored_keyring_key(user_uuid, master_password_fernet_key)
        if stored_keyring_key != keyring_key:
            # Cleanup the created files ?
            raise HTTPException(status_code=500, detail="Error encrypting and storing keyring key, aborting keyring creation. This should never happen.")
        # Validate the keyring
        _ = decrypt_keyring(user_uuid, stored_keyring_key)

        return keyring_key
    except Exception as e:
        logger.error(f"Error initializing new keyring: {e}")
        raise HTTPException(status_code=500, detail="Error initializing new keyring")