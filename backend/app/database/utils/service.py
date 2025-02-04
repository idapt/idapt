from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException
from sqlalchemy import create_engine
import logging
from app.database.utils.migration_manager import run_migrations
import os
from cryptography.fernet import Fernet

logger = logging.getLogger("uvicorn")

def create_session(db_path: str, script_location: str, models_declarative_base_class) -> Session:
    """Create a new database session"""
    try:
        # Check if database file exists and create empty one if not
        if not os.path.exists(db_path):
            
            # Create folder for the database
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with open(db_path, 'w') as f:
                pass

        engine = create_engine(
            "sqlite:///" + db_path,
            connect_args={
                "check_same_thread": False,
                "timeout": 30  # SQLite busy timeout in seconds
            }
        )
        
        # Run migrations if needed
        run_migrations(engine, db_path, script_location, models_declarative_base_class)
        
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        return SessionLocal()
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@contextmanager
def get_encrypted_database_session(db_path: str, script_location: str, models_declarative_base_class, database_file_encryption_key: str) -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    
    try:
        try:
            # Decrypt the database file
            with open(db_path, 'rb') as f:
                encrypted_data = f.read()
        
            # Decrypt the database file data
            database_file_fernet = Fernet(database_file_encryption_key)
            decrypted_data = database_file_fernet.decrypt(encrypted_data)
                
            # Move the database file to a temporary file with the .old extension for recovery in case of failure
            os.rename(db_path, db_path + ".old")

            # Write the decrypted data to a new file at the same path with the .decrypted extension
            with open(db_path, 'wb') as f:
                f.write(decrypted_data)
        except Exception as e:
            # In case of an error here just rename the .old file to the original file if it exists
            if os.path.exists(db_path + ".old"):
                os.rename(db_path + ".old", db_path)
            logger.error(f"Database decryption error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        
        try:
            # Create a new database session on the decrypted database file
            session = create_session(db_path, script_location, models_declarative_base_class)

            yield session

        except Exception as e:
            # In case of an error here, the error is not encryption related so we will still try to encrypt the database file after and save its new version
            logger.error(f"Database session error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            try:
                # Move the decrypted database file to a temporary file with the .decrypted extension for recovery in case of failure
                os.rename(db_path, db_path + ".decrypted")

                # Encrypt the database file again using the same key # TODO Add key rotation
                encrypted_data = database_file_fernet.encrypt(decrypted_data)
                # Test if the encrypted data is valid ?
                #database_file_fernet.decrypt(encrypted_data)
                
                # Write the encrypted data to the original database file path
                with open(db_path, 'wb') as f:
                    f.write(encrypted_data)
                # Delete the decrypted database file
                os.remove(db_path + ".decrypted")
                # Delete the old database file
                os.remove(db_path + ".old")

            except Exception as e:
                # An error here means there is an issue with the re-encryption of the modified database file, best we can do is to revert to the old version but this should not happen
                if os.path.exists(db_path + ".old"):
                    os.rename(db_path + ".old", db_path)
                # Delete the decrypted database file
                if os.path.exists(db_path + ".decrypted"):
                    os.remove(db_path + ".decrypted")
                logger.error(f"Database re-encryption error, this should not happen: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # In case of an error, retry encryption 
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@contextmanager
def get_session(db_path: str, script_location: str, models_declarative_base_class) -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    try:    
        # Create a new database session
        session = create_session(db_path, script_location, models_declarative_base_class)

        yield session

    finally:
        session.close()