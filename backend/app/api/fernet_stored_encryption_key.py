import os
from cryptography.fernet import Fernet
from fastapi import HTTPException
import logging

logger = logging.getLogger("uvicorn")

class FernetStoredEncryptionKey:

    @staticmethod
    def create_new_random_key_and_store_it(stored_key_path: str, kek: bytes, overwrite_safely: bool = True) -> bytes:
        """
        Creates a new key and stores it in the keyring key file.
        Returns the key.
        """
        try:
            key = Fernet.generate_key()
            FernetStoredEncryptionKey.store_encrypted_key_at_path(
                key=key, 
                kek=kek, 
                stored_key_path=stored_key_path, 
                overwrite_safely=overwrite_safely
            )
            return key
        except Exception as e:
            logger.error(f"Error creating new key at path: {stored_key_path}: {e}")
            raise HTTPException(status_code=500, detail="Error creating new key")
    
    @staticmethod
    def load_decrypted_stored_key(stored_key_path: str, kek: bytes) -> bytes:
        """
        Loads a decrypted key from a stored key path and a stored key encryption key.
        """
        try:
            key = FernetStoredEncryptionKey.get_decrypted_stored_key_from_path(stored_key_path=stored_key_path, kek=kek)
            return key
        
        except Exception as e:
            logger.error(f"Error loading decrypted stored key at path: {stored_key_path}: {e}")
            raise HTTPException(status_code=500, detail="Error loading decrypted stored key")
        
    @staticmethod
    def store_encrypted_key_at_path(key: bytes | str, kek: bytes, stored_key_path: str, overwrite_safely: bool = True) -> None:
        """
        Encrypts the key and saves it to the key file path using the key encryption key.
        """
        try:
            if not isinstance(kek, bytes):
                raise HTTPException(status_code=500, detail="Error encrypting and storing key, kek is not of type bytes")
            # Create a fernet with the kek
            kek_fernet = Fernet(kek)
            # Encrypt the key 
            key_encrypted = kek_fernet.encrypt(key)

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(stored_key_path), exist_ok=True)

            # If there is already a file at the stored key path, move it to a .prev file
            if os.path.exists(stored_key_path) and overwrite_safely:
                # Move the old file to a .prev file for recovery in case of failure
                os.rename(stored_key_path, stored_key_path + ".prev")
            elif os.path.exists(stored_key_path) and not overwrite_safely:
                raise HTTPException(status_code=500, detail="Error storing new encrypted key, file already exists")
            
            # Save the encrypted key bytes to the file in binary mode
            with open(stored_key_path, "wb") as f:
                f.write(key_encrypted)
            
            # Get the decrypted key to be sure that the stored key is valid
            decrypted_key = FernetStoredEncryptionKey.get_decrypted_stored_key_from_path(
                stored_key_path=stored_key_path,
                kek=kek
            )
            if decrypted_key != key:
                raise HTTPException(status_code=500, detail="Error decrypting stored key, aborting key creation. This should never happen.")
            
            # Delete the .prev file if it exists
            if os.path.exists(stored_key_path + ".prev"):
                os.remove(stored_key_path + ".prev")
                
        except Exception as e:
            logger.error(f"Error encrypting and storing key at path: {stored_key_path}: {e}")
            # If there is a .prev file, restore it
            if os.path.exists(stored_key_path + ".prev"):
                os.rename(stored_key_path + ".prev", stored_key_path)
            raise HTTPException(status_code=500, detail="Error encrypting and storing key")

    @staticmethod
    def get_decrypted_stored_key_from_path(stored_key_path: str, kek: bytes) -> bytes:
        """
        Decrypts the stored key.
        """
        try:
            if not isinstance(kek, bytes):
                raise HTTPException(status_code=500, detail="Error decrypting stored key, kek is not of type bytes")
            # Create a fernet with the kek
            kek_fernet = Fernet(kek)
            # Decrypt the key in binary mode
            with open(stored_key_path, "rb") as f:
                key : bytes = kek_fernet.decrypt(f.read())
            return key
        except Exception as e:
            logger.error(f"Error decrypting stored key at path: {stored_key_path}: {e}")
            raise HTTPException(status_code=500, detail="Error decrypting stored key")

