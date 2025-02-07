from contextlib import contextmanager
from pathlib import Path
from typing import Generator, AsyncGenerator, List
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException
from sqlalchemy import create_engine
import logging
from app.api.migration_manager import run_migrations
import os
from app.api.aes_gcm_file_encryption import decrypt_file_aes_gcm, encrypt_file_aes_gcm
from sqlalchemy import Engine
from pydantic import BaseModel, ConfigDict
import asyncio
from asyncio import Lock

logger = logging.getLogger("uvicorn")

CACHE_ENGINE_NO_ACTIVE_SESSIONS_COUNT_DOWN_SECONDS = 30
CACHE_ENGINE_CREATION_SESSION_TIMEOUT_SECONDS = 10

class CachedEngine(BaseModel):
    engine: Engine
    active_sessions: List[Session]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, engine: Engine, active_sessions: List[Session]):
        super().__init__(engine=engine, active_sessions=active_sessions)

encrypted_database_cached_engines: dict[str, CachedEngine] = {}
encrypted_database_creation_locks: dict[str, Lock] = {}
pending_engine_creations: set[str] = set()

@asynccontextmanager
async def get_session_from_cached_database_engine(db_path: str, script_location: str, models_declarative_base_class, dek: str) -> AsyncGenerator[Session, None]:
    """
    Get a database session from an encrypted database engine
    """
    try:
        # TODO
        # Check if there is an existing cached database for this database file
        if db_path not in encrypted_database_cached_engines:
            # If there is not already a creation in progress for this database file
            if db_path not in pending_engine_creations:
                # If there is not already a lock for the creation of the engine, create one
                if db_path not in encrypted_database_creation_locks:
                    encrypted_database_creation_locks[db_path] = Lock()
                # Wait for the lock to be released
                async with encrypted_database_creation_locks[db_path]:
                    # If there is not already a creation in progress for this database file
                    if db_path not in encrypted_database_cached_engines and db_path not in pending_engine_creations:
                        # Add the database file to the pending creations to know it is currently being created
                        pending_engine_creations.add(db_path)
                        # Create the engine in a separate asyncio task
                        asyncio.create_task(encrypted_database_engine_manager(db_path, script_location, models_declarative_base_class, dek))
        
        # Wait for the engine to be created and cached
        while db_path in pending_engine_creations:
            await asyncio.sleep(0.2)

        if db_path not in encrypted_database_cached_engines or encrypted_database_cached_engines[db_path].engine is None:
            raise HTTPException(status_code=500, detail="Cannot get session cached engine has not been created successfully")

        # Get the new cached engine
        engine = encrypted_database_cached_engines[db_path].engine

    except Exception as e:
        logger.error(f"Error in get_session_from_cached_database_engine: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    try:
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        session = SessionLocal()
        # Add the session to the cached engine active sessions
        encrypted_database_cached_engines[db_path].active_sessions.append(session)

        yield session

    finally:
        try:
            if session is not None:
                session.close()
                # Remove the session from the cached engine
                encrypted_database_cached_engines[db_path].active_sessions.remove(session)
        except Exception as e:
            logger.error(f"Error in get_session_from_cached_database_engine: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

async def encrypted_database_engine_manager(db_path: str, script_location: str, models_declarative_base_class, dek: str) -> Engine:
    """
    Context manager for encrypted database engine
    The engine is cached for the whole time there is active sessions on it
    Once there is no active sessions for at least 30 seconds, the engine and database are terminated
    Only one engine per database file is allowed to be open at a time
    """

    #if os.path.exists(db_path + ".decrypted"):
    #    raise HTTPException(status_code=500, detail="Database file is already decrypted and in use")

    try:
        # Add the database file to the pending creations to know it is currently being created
        if db_path not in pending_engine_creations:
            pending_engine_creations.add(db_path)
        # Check if database file exists and create empty one if not
        if not os.path.exists(db_path + ".encrypted"):            
            # If there is a .old file, rename it to the original encrypted db file as there has been an error
            if os.path.exists(db_path + ".old"):
                # TODO Add try of encryption key on it here before recovery
                os.rename(db_path + ".old", db_path + ".encrypted")
            # If there is a decrypted file and there is no .old file, rename the decrypted file to the original file
            elif os.path.exists(db_path):
                # TODO do sanity check of the decrypted file before recovery
                # TODO Check the existing associated journal and either apply or rollback changesso that db state is consistent
                #os.rename(db_path + ".decrypted", db_path)
                # Save the decrypted database file encrypted with the dek
                encrypt_file_aes_gcm(db_path, db_path + ".encrypted", dek)
                # Delete the decrypted database file
                os.remove(db_path)
            # If there is no .old file or .decrypted file, create an empty database file
            else:
                # Create required directories
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                # Create empty database file
                with open(db_path, 'w') as f:
                    pass
                # Encrypt the database file with the dek
                encrypt_file_aes_gcm(db_path, db_path + ".encrypted", dek)
                # Delete the decrypted database file
                os.remove(db_path)
                
    except Exception as e:
        logger.error(f"Database file creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # Decrypt the database file
    try:
        # Decrypt the database file to the same path with the decrypted extension
        decrypt_file_aes_gcm(db_path + ".encrypted", db_path, dek)

        # TODO Implement key rotation here

        # Move the encrypted file to the .old file to keep it as a backup and make place for the new encrypted file
        os.rename(db_path + ".encrypted", db_path + ".old")

    except Exception as e:
        # In case of an error here abort the decryption and delete the decrypted file
        if os.path.exists(db_path):
            os.remove(db_path)
        # If the .old file exists, rename it to the original encrypted db file as there has been an error
        if os.path.exists(db_path + ".old"):
            os.rename(db_path + ".old", db_path + ".encrypted")
        logger.error(f"Database decryption error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Create a new database engine on the decrypted database file and cache it
    try:
        url = "sqlite:///" + db_path

        engine = create_engine(
            url,
            connect_args={
                "timeout": 30  # SQLite busy timeout in seconds
            }
        )

        # Run migrations on the engine with a dedicated connection before making the engine avaliable
        with engine.begin() as connection:
            run_migrations(
                connection=connection,
                connection_string=url,
                script_location=script_location,
                models_declarative_base_class=models_declarative_base_class
            )

        cached_engine = CachedEngine(engine=engine, active_sessions=[])
        # Cache the engine in the global variable with the db path as the key as it is unique for each database and user_uuid
        encrypted_database_cached_engines[db_path] = cached_engine

    except Exception as e:
        # In case of an error here, the error is not encryption related so we will still try to encrypt the database file after and save its new version
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Remove the database file from the pending creations as it is no longer being created and is cached or not sucessfully created
        pending_engine_creations.discard(db_path)

    try:
        while True:
            # Check every 2 seconds if there are no active sessions on the engine
            await asyncio.sleep(2)
            if len(encrypted_database_cached_engines[db_path].active_sessions) == 0:
                logger.info(f"No active sessions on the engine for the database {db_path}, beginning countdown for {CACHE_ENGINE_NO_ACTIVE_SESSIONS_COUNT_DOWN_SECONDS} seconds to close the engine")
                # If there are no active sessions, begin a countdown to 30 seconds to close the engine
                should_close_engine = False
                for i in range(CACHE_ENGINE_NO_ACTIVE_SESSIONS_COUNT_DOWN_SECONDS, 0, -1):
                    if len(encrypted_database_cached_engines[db_path].active_sessions) != 0:
                        logger.info(f"Active sessions on the engine for the database {db_path}, stopping countdown")
                        # A new active session has been created, reset the countdown and get out of the countdown loop
                        should_close_engine = False
                        # Get out of the countdown loop
                        break
                    if i <= 1:
                        logger.info(f"No active sessions on the engine for the database {db_path} for {CACHE_ENGINE_NO_ACTIVE_SESSIONS_COUNT_DOWN_SECONDS} seconds, closing the engine")
                        should_close_engine = True
                        break
                    await asyncio.sleep(1)
                if should_close_engine:
                    # Get out of the active sessions checking loop and close the engine
                    break

    except Exception as e:
        logger.error(f"Error in encrypted database engine manager active sessions checking loop for {db_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Encrypt the database file again using the same key
        try:
            # Encrypt the database file again using AES-GCM with the same key # TODO Add key rotation
            encrypt_file_aes_gcm(db_path, db_path + ".encrypted", dek)
            # Everything is ok, delete the decrypted and old database files
            os.remove(db_path)
            os.remove(db_path + ".old")

        except Exception as e:
            # An error here means there is an issue with the re-encryption of the modified database file, best we can do is to revert to the old version but this should not happen
            if os.path.exists(db_path + ".old"):
                # TODO Add try of encryption key on it here before recovery
                os.rename(db_path + ".old", db_path + ".encrypted")
            # Delete the decrypted database file
            if os.path.exists(db_path):
                os.remove(db_path)
            logger.error(f"Database re-encryption error for {db_path}, some database modifications may be lost, database was restored to the previous version, this should not happen: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Remove the engine from cached engines
            encrypted_database_cached_engines.pop(db_path)


# Unused, kept for reference
@contextmanager
def get_session(db_path: str, script_location: str, models_declarative_base_class) -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    try:
        # Check if database file exists and create empty one if not
        if not os.path.exists(db_path):            
            # Create folder for the database
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with open(db_path, 'w') as f:
                pass

        connection_string = "sqlite:///" + db_path

        engine = create_engine(
            connection_string,
            connect_args={
                "check_same_thread": False,
                "timeout": 30  # SQLite busy timeout in seconds
            }
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        session = SessionLocal()
        
        # Run migrations if needed
        run_migrations(
            session=session,
            connection_string=connection_string,
            script_location=script_location,
            models_declarative_base_class=models_declarative_base_class
        )

        yield session

    finally:
        session.close()