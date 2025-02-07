from app.auth.schemas import AccessSKTokenData, Keyring
from fastapi import Depends, HTTPException
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from cryptography.fernet import Fernet
import logging
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.api.fernet_stored_encryption_key import FernetStoredEncryptionKey
import uuid
import shutil
from cachetools.func import ttl_cache

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

DATA_FOLDER_PATH = "/data"
USER_DATA_FOLDER_PATH = "/data/{user_uuid}"
USER_UUID_TEST_FILE_PATH = "/data/{user_uuid}/keys/user_uuid_test.txt"
KEK_P_MK_PATH = "/data/{user_uuid}/keys/kek_p_mk.txt"
SK_DIR_PATH = "/data/{user_uuid}/keys/session_keys"
SK_KEK_P_PATH_TEMPLATE = "/data/{user_uuid}/keys/session_keys/sk_kek_p_{sk_uuid}.txt"
KEK_S_PATH_TEMPLATE = "/data/{user_uuid}/keys/session_keys/kek_s_{sk_uuid}.txt"
KEK_P_KEK_S_PATH_TEMPLATE = "/data/{user_uuid}/keys/session_keys/kek_p_kek_s_{sk_uuid}.txt"


KEK_DATASOURCES_KEK_P_PATH = "/data/{user_uuid}/keys/kek_datasources.txt"
KEK_PROCESSING_KEK_P_PATH = "/data/{user_uuid}/keys/kek_processing.txt"
KEK_PROCESSING_STACKS_KEK_P_PATH = "/data/{user_uuid}/keys/kek_processing_stacks.txt"
KEK_SETTINGS_KEK_P_PATH = "/data/{user_uuid}/keys/kek_settings.txt"

def register_new_user(user_uuid: str, hashed_password: str) -> AccessSKTokenData:
    """
    Register a new user
    """
    try:
        # TODO Implement a register flow with admin token for the hosted version so that we can control user registration
        # Check if the maximum number of public users for this host is reached
        number_of_users = len(os.listdir(DATA_FOLDER_PATH))
        if number_of_users >= int(os.environ.get("MAX_PUBLIC_USERS_FOR_THIS_HOST")):
            raise Exception("Maximum number of public users reached for this host")

        # Check if the user already exists by checking if the kek_p_mk file exists
        if os.path.exists(KEK_P_MK_PATH.format(user_uuid=user_uuid)):
            raise Exception("User already exists")

        logger.info(f"Creating new kek_p for user {user_uuid}")

        # Get the master key from the password
        mk = get_mk_from_password(user_uuid, hashed_password)  

        # Create the user data folder
        os.makedirs(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid), exist_ok=True)
        # TODO Move this to separate flow with stripe validation for hosted
        # Create a new kek_p stored encrypted with the master key
        initial_kek_p = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
            stored_key_path=KEK_P_MK_PATH.format(user_uuid=user_uuid),
            kek=mk
        )
        # Create the user_uuid_test_file with the initial kek_p
        FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=user_uuid.encode(),
            kek=initial_kek_p,
            stored_key_path=USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid),
            overwrite_safely=True
        )

        # Get a new session key with the password
        token_data = get_new_access_sk_token_with_password(user_uuid, hashed_password)

        # Return the token data
        return token_data
    
    except Exception as e:
        logger.error(f"Error registering new user: {e}")
        if "Maximum number of public users reached for this host" in str(e):
            raise HTTPException(status_code=429, detail="Maximum number of public users reached for this host, delete existing users first or increase the MAX_PUBLIC_USERS_FOR_THIS_HOST environment variable")
        elif "User already exists" in str(e):
            raise HTTPException(status_code=400, detail="User already exists")
        else:
            # There has been an error, delete the newly created user data folder ? Can be a security risk TODO
            raise HTTPException(status_code=500, detail="Error registering new user")

def get_new_access_sk_token_with_password(user_uuid: str, hashed_password: str) -> AccessSKTokenData:
    """
    Get a new session key with the password.
    Each time this is called the kek_p is rotated with all other keys encrypted with it (sk_*, keyring_json) and that decrypt it (kek_p_mk, kek_p_kek_s_*)
    """
    try:
        logger.info(f"Getting new access sk token with password for user {user_uuid}")
        # Get the master key from the password
        mk = get_mk_from_password(user_uuid, hashed_password)  

        # Check if the kek_p_mk file exists
        kek_p_mk_path = KEK_P_MK_PATH.format(user_uuid=user_uuid)
        if not os.path.exists(kek_p_mk_path):
            raise Exception("Unknown user")
        
        # Decrypt the kek_p_mk using the mk
        old_kek_p = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=kek_p_mk_path,
            kek=mk
        )

        # Try to decrypt the user_uuid_test_file using the old kek_p to see if it is valid
        test_kek_p_with_user_uuid_test_file(user_uuid=user_uuid, kek_p=old_kek_p)
            
        # If it exists, rotate the kek_p as we have the mk
        new_kek_p = rotate_kek_p(user_uuid=user_uuid, old_kek_p=old_kek_p, mk=mk)
        logger.debug(f"New kek_p: {new_kek_p}")

        # Create a new sk with the new kek_p
        sk_uuid, sk = create_new_sk_with_kek_p(user_uuid=user_uuid, kek_p=new_kek_p)
        logger.debug(f"New sk: {sk}")
  
        # Create the token data and send the current keyring key to the user
        token_data = AccessSKTokenData(
            user_uuid=user_uuid,
            sk_uuid=sk_uuid,
            sk_str=sk.decode()
        )
        return token_data
    
    except Exception as e:
        logger.error(f"Error getting new access sk token with password: {e}")
        if "Invalid kek_p" in str(e) or "Unknown user" in str(e):
            raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
        else:
            raise HTTPException(status_code=500, detail="Error getting new access sk token with password")

def get_keyring_with_access_sk_token_from_auth_header(token: Annotated[str, Depends(oauth2_scheme)]) -> Keyring:
    """
    Get the keyring with the token from the auth header
    """
    return get_keyring_with_access_sk_token(token)

@ttl_cache(maxsize=512, ttl=30)
def get_keyring_with_access_sk_token(token: str) -> Keyring:
    """
    Get the keyring with the token
    The keyring is cached for 30 seconds to avoid re-reading and decrypting the keyring from the disk and reuse the same keyring
    Only in the case of a keyring dek rotation we need to invalidate the cache TODO
    """
    try:

        # Decode the token to get the keyring key # JWT Needed here ?
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Get the keyring encryption key from the payload
        user_uuid: str = payload.get("user_uuid")
        sk_uuid: str = payload.get("sk_uuid")
        sk_str: str = payload.get("sk_str")
        sk: bytes = sk_str.encode()
        # Recreate the token data to validate it with pydantic # Needed ?
        access_sk_token_data = AccessSKTokenData(
            user_uuid=user_uuid,
            sk_uuid=sk_uuid,
            sk_str=sk_str
        )

        # Check if the user exists
        if not os.path.exists(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid)) or not os.path.exists(USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid)):
            raise Exception("Invalid token")
        
        kek_p = get_kek_p_with_sk(
            user_uuid=user_uuid,
            sk_uuid=sk_uuid,
            sk=sk
        )

        # Test the kek_p with the user_uuid_test_file
        test_kek_p_with_user_uuid_test_file(user_uuid=user_uuid, kek_p=kek_p)

        # Decrypt the keyring with the kek_p
        keyring = get_keyring_with_kek_p(user_uuid=user_uuid, kek_p=kek_p)

        # Return the keyring
        return keyring

    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    except Exception as e:
        if "Invalid kek_p" in str(e) or "Invalid token" in str(e):
            raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
        else:
            logger.error(f"Error getting keyring with sk token: {e}")
            raise HTTPException(status_code=500, detail="Error getting keyring with sk token")



def get_mk_from_password(user_uuid: str, password: str) -> bytes:
    """Convert a password into a master key that can be used as a Fernet key"""
    try:
        # Use PBKDF2 to derive a 32-byte key from the password
        user_specific_salt = user_uuid.encode() + 'static_salt_part'.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_specific_salt,
            iterations=100000,
        )
        # Derive the key and encode it properly for Fernet usage
        key = kdf.derive(password.encode())
        mk = base64.urlsafe_b64encode(key)
        return mk
    except Exception as e:
        logger.error(f"Error getting mk from password: {e}")
        raise HTTPException(status_code=500, detail="Error getting mk from password")


def create_new_sk_with_kek_p(user_uuid: str, kek_p: bytes) -> tuple[str, bytes]:
    """
    Creates a new session key and store it with the kek_p.
    Returns the sk uuid and the sk.
    """
    try:
        logger.info(f"Creating new sk with kek_p for user {user_uuid}")
        # Generate a new session key uuid that does not already exist
        sk_uuid = None
        while sk_uuid is None or os.path.exists(SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
            sk_uuid = str(uuid.uuid4())

        # Generate a random new session key and store it with the kek_p into sk_kek_p_{sk_uuid}
        sk = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
            stored_key_path=SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
            kek=kek_p
        )

        # Create a new kek_s for this session key and store it encrypted with the session key into kek_s_{sk_uuid}
        kek_s = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
            stored_key_path=KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
            kek=sk
        )
        # Encrypt the kek_p in a new kek_p_kek_s for this sk so that we can access the kek_p using the sk into kek_p_kek_s_{sk_uuid}
        kek_p_kek_s = FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=kek_p,
            kek=kek_s,
            stored_key_path=KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
            overwrite_safely=True
        )
        # Return the sk uuid and the sk
        return sk_uuid, sk
    
    except Exception as e:
        logger.error(f"Error creating new session key: {e}")
        # Cleanup potentially created files
        try:
            if sk_uuid is not None and os.path.exists(SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
                os.remove(SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
            if kek_s is not None and os.path.exists(KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
                os.remove(KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
            if kek_p_kek_s is not None and os.path.exists(KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
                os.remove(KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
        except Exception as e:
            logger.error(f"Error cleaning up potentially created files: {e}")
        raise HTTPException(status_code=500, detail="Error creating new session key")

def rotate_kek_p(user_uuid: str, old_kek_p: bytes, mk: bytes) -> bytes:
    """
    Rotates the kek_p and all keys it encrypts (sk_*, service_keks_*/keyring) and all keys used to get it (kek_p_mk, kek_p_kek_s_*)
    """
    try:
        logger.info(f"Rotating kek_p for user {user_uuid}")

        # Move the old kek_p to a .backup file
        os.rename(KEK_P_MK_PATH.format(user_uuid=user_uuid), KEK_P_MK_PATH.format(user_uuid=user_uuid) + ".backup")
        # Move the old user_uuid_test_file to a .backup file
        os.rename(USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid), USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid) + ".backup")
        
        # Create a new kek_p and store it with the mk
        new_kek_p = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
            stored_key_path=KEK_P_MK_PATH.format(user_uuid=user_uuid),
            kek=mk
        )
        
        # Decrypt the keyring using the old kek_p
        keyring = get_keyring_with_kek_p(user_uuid=user_uuid, kek_p=old_kek_p)

        # Encrypt the keyring using the new keyring key # TODO Implement backup for this
        encrypt_keyring_with_kek_p(user_uuid=user_uuid, kek_p=new_kek_p, keyring=keyring)

        # Create a new user_uuid_test_file with the new kek_p
        FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=user_uuid.encode(),
            kek=new_kek_p,
            stored_key_path=USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid),
            overwrite_safely=True
        )
        # Test the new kek_p with the user_uuid_test_file
        test_kek_p_with_user_uuid_test_file(user_uuid=user_uuid, kek_p=new_kek_p)
        
        # For each existing sk, decrypt it and its corresponding kek_s using the old kek_p and encrypt it using the new kek_p
        # For each file in the session_keys directory, decrypt it using the old kek_p and encrypt it using the new kek_p
        if os.path.exists(SK_DIR_PATH.format(user_uuid=user_uuid)):
            for sk_file in os.listdir(SK_DIR_PATH.format(user_uuid=user_uuid)):
                try:
                    # If this is a session key file
                    if sk_file.startswith("sk_kek_p_"):
                        # Get the sk_uuid from the file name
                        sk_uuid = sk_file.split("_")[3].split(".")[0]
                        logger.info(f"Rotating session key {sk_uuid}")
                        
                        # Get the required sk info for rotation
                        # Decrypt the stored sk from sk_kek_p using the old kek_p
                        # sk is never rotated
                        sk = FernetStoredEncryptionKey.load_decrypted_stored_key(
                            stored_key_path=SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
                            kek=old_kek_p
                        )
                        # Decrypt the corresponding kek_s using the sk
                        old_kek_s = FernetStoredEncryptionKey.load_decrypted_stored_key(
                            stored_key_path=KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
                            kek=sk
                        )
                        # Remove the old sk_kek_p
                        os.remove(SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
                        # Remove the old kek_s
                        os.remove(KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
                        # Remove the old kek_p_kek_s
                        os.remove(KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))

                        # Store the sk using the new kek_p as the encryption key
                        FernetStoredEncryptionKey.store_encrypted_key_at_path(
                            key=sk,
                            kek=new_kek_p,
                            stored_key_path=SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
                            overwrite_safely=True
                        )
                        # Rotate the kek_s using the sk while we are at it
                        new_kek_s = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
                            stored_key_path=KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
                            kek=sk,
                            overwrite_safely=True # Overwrite safely the old kek_s file
                        )

                        # Create the new kek_p_kek_s file by storing the new_kek_p encrypted with new_kek_s
                        new_kek_p_kek_s = FernetStoredEncryptionKey.store_encrypted_key_at_path(
                            key=new_kek_p,
                            kek=new_kek_s,
                            stored_key_path=KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
                            overwrite_safely=True
                        )
                        # Test the new sk flow to get the kek p and check that it is correct
                        new_kek_p_got_from_sk = get_kek_p_with_sk(user_uuid=user_uuid, sk_uuid=sk_uuid, sk=sk)
                        test_kek_p_with_user_uuid_test_file(user_uuid=user_uuid, kek_p=new_kek_p_got_from_sk)

                except Exception as e:
                    logger.error(f"Error rotating session key {sk_file}: {e}")
                    # If there is an error, delete this session key
                    # It should not happen often
                    if os.path.exists(SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
                        os.remove(SK_KEK_P_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
                    if os.path.exists(KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
                        os.remove(KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
                    if os.path.exists(KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid)):
                        os.remove(KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid))
                    raise HTTPException(status_code=500, detail="Error rotating session key")

        # Everything went well delete the .backup files
        os.remove(KEK_P_MK_PATH.format(user_uuid=user_uuid) + ".backup")
        os.remove(USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid) + ".backup")

        # Return the new kek_p
        return new_kek_p
    
    except Exception as e:
        # If something goes wrong, restore the old files so that we can still decrypt the keyring with the old keyring key with the master password
        # TODO Implement recovery codes given to the user and add other keyring keys encrypted with them so that if the user loose access to his master_password he can still recover his data using these.
        if os.path.exists(KEK_P_MK_PATH.format(user_uuid=user_uuid) + ".backup"):
            os.rename(KEK_P_MK_PATH.format(user_uuid=user_uuid) + ".backup", KEK_P_MK_PATH.format(user_uuid=user_uuid))
        if os.path.exists(USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid) + ".backup"):
            os.rename(USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid) + ".backup", USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid))
        logger.error(f"Error rotating kek_p: {e}")
        raise HTTPException(status_code=500, detail="Error rotating kek_p")

def init_new_keyring_service_keks_if_needed(user_uuid: str, kek_p: bytes) -> None:
    """
    Initializes a new keyring for a user using the master key.
    Returns the kek_p used to encrypt the keyring.
    """
    try:
        # Create a new kek for each service if needed stored encrypted with the kek_p
        if not os.path.exists(KEK_DATASOURCES_KEK_P_PATH.format(user_uuid=user_uuid)):
            _ = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
                stored_key_path=KEK_DATASOURCES_KEK_P_PATH.format(user_uuid=user_uuid),
                kek=kek_p
            )
        if not os.path.exists(KEK_PROCESSING_KEK_P_PATH.format(user_uuid=user_uuid)):
            _ = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
                stored_key_path=KEK_PROCESSING_KEK_P_PATH.format(user_uuid=user_uuid),
                kek=kek_p
            )
        if not os.path.exists(KEK_PROCESSING_STACKS_KEK_P_PATH.format(user_uuid=user_uuid)):
            _ = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
                stored_key_path=KEK_PROCESSING_STACKS_KEK_P_PATH.format(user_uuid=user_uuid),
                kek=kek_p
            )
        if not os.path.exists(KEK_SETTINGS_KEK_P_PATH.format(user_uuid=user_uuid)):
            _ = FernetStoredEncryptionKey.create_new_random_key_and_store_it(
                stored_key_path=KEK_SETTINGS_KEK_P_PATH.format(user_uuid=user_uuid),
                kek=kek_p
            )
            
    except Exception as e:
        logger.error(f"Error initializing new keyring: {e}")
        # try to clean up the potentially created files
        try:
            if os.path.exists(KEK_P_MK_PATH.format(user_uuid=user_uuid)):
                os.remove(KEK_P_MK_PATH.format(user_uuid=user_uuid))
        except Exception as e:
            logger.error(f"Error cleaning up potentially created files: {e}")
        raise HTTPException(status_code=500, detail="Error initializing new keyring")


def get_kek_p_with_sk(user_uuid: str, sk_uuid: str, sk: bytes) -> bytes:
    """
    Decrypts the keyring from the keyring file using the session key provided.
    """
    try:
        # Decrypt the kek_s with the sk
        kek_s = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
            kek=sk
        )

        # Decrypt the corresponding kek_p_kek_s with the kek_s to get the kek_p
        kek_p = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=KEK_P_KEK_S_PATH_TEMPLATE.format(user_uuid=user_uuid, sk_uuid=sk_uuid),
            kek=kek_s
        )

        return kek_p
    
    except Exception as e:
        logger.error(f"Error decrypting keyring with sk: {e}")
        raise HTTPException(status_code=500, detail="Error decrypting keyring with sk")
    
def get_keyring_with_kek_p(user_uuid: str, kek_p: bytes) -> Keyring:
    """
    Decrypts the keyring from the keyring file using the keyring key provided.
    """
    try:     
        # Initialize the keyring service keks
        init_new_keyring_service_keks_if_needed(user_uuid=user_uuid, kek_p=kek_p)

        # Decrypt all individual services keks using the kek_p
        kek_datasources = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=KEK_DATASOURCES_KEK_P_PATH.format(user_uuid=user_uuid),
            kek=kek_p
        )
        kek_processing = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=KEK_PROCESSING_KEK_P_PATH.format(user_uuid=user_uuid),
            kek=kek_p
        )
        kek_processing_stacks = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=KEK_PROCESSING_STACKS_KEK_P_PATH.format(user_uuid=user_uuid),
            kek=kek_p
        )
        kek_settings = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=KEK_SETTINGS_KEK_P_PATH.format(user_uuid=user_uuid),
            kek=kek_p
        )

        # Create the keyring with the decrypted services keks
        keyring = Keyring(
            user_uuid=user_uuid,
            kek_datasources=kek_datasources,
            kek_processing=kek_processing,
            kek_processing_stacks=kek_processing_stacks,
            kek_settings=kek_settings
        )

        return keyring

    except Exception as e:
        logger.error(f"Error decrypting keyring, wrong kek_p: {e}")
        raise HTTPException(status_code=500, detail="Error decrypting keyring, wrong kek_p")


def encrypt_keyring_with_kek_p(user_uuid: str, kek_p: bytes, keyring: Keyring) -> None:
    """
    Encrypts the keyring and saves it to the keyring file using the keyring key provided.
    """
    try:
        # TODO see overwrite_safely
        # Encrypt and store all individual services keks using the kek_p
        _ = FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=keyring.kek_datasources,
            kek=kek_p,
            stored_key_path=KEK_DATASOURCES_KEK_P_PATH.format(user_uuid=user_uuid)
        )
        _ = FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=keyring.kek_processing,
            kek=kek_p,
            stored_key_path=KEK_PROCESSING_KEK_P_PATH.format(user_uuid=user_uuid)
        )
        _ = FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=keyring.kek_processing_stacks,
            kek=kek_p,
            stored_key_path=KEK_PROCESSING_STACKS_KEK_P_PATH.format(user_uuid=user_uuid)
        )
        _ = FernetStoredEncryptionKey.store_encrypted_key_at_path(
            key=keyring.kek_settings,
            kek=kek_p,
            stored_key_path=KEK_SETTINGS_KEK_P_PATH.format(user_uuid=user_uuid)
        )

    except Exception as e:
        logger.error(f"Error encrypting keyring: {e}")
        raise HTTPException(status_code=500, detail="Error encrypting keyring")


def test_kek_p_with_user_uuid_test_file(user_uuid: str, kek_p: bytes) -> None:
    """
    Tests the kek_p with the user_uuid_test_file to ensure that the kek_p is correct.
    Raise if the kek_p is wrong.
    """
    try:
        # Load the user_uuid_test_file
        user_uuid_test_file_content_encoded = FernetStoredEncryptionKey.load_decrypted_stored_key(
            stored_key_path=USER_UUID_TEST_FILE_PATH.format(user_uuid=user_uuid),
            kek=kek_p
        )
        user_uuid_test_file_content = user_uuid_test_file_content_encoded.decode()

        # If the user_uuid_test_file is not the same as the user_uuid, raise an error
        if user_uuid_test_file_content != user_uuid:
            raise Exception("Invalid kek_p")
        #else:
            #logger.debug(f"kek_p and credentials are valid for user {user_uuid}")

    except Exception as e:
        logger.error(f"Error testing kek_p with user_uuid_test_file: {e}")
        raise e


def delete_user(user_uuid: str) -> None:
    """
    Deletes the user from the database.
    """
    try:
        # The keyring is valid and user is authenticated so we can delete the user data
        if os.path.exists(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid)):
            shutil.rmtree(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid))
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Error deleting user, user is probably partially deleted")



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