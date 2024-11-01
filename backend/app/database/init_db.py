import os
import secrets
import string
import psycopg2
from psycopg2 import sql
import logging
from urllib.parse import quote_plus
import alembic
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text, inspect
from app.database.models import Base
from app.database.connection import get_connection_string


logger = logging.getLogger(__name__)

def generate_random_password(length=32):
    try:
        characters = string.ascii_letters + string.digits # No special characters for now as they cause errors in the database connection string
        password = ''.join(secrets.choice(characters) for i in range(length))
        logger.debug("Successfully generated random password")
        return password
    except Exception as e:
        logger.error(f"Error generating random password: {e}", exc_info=True)
        raise

def change_superuser_password():
    password_dir = "/backend/secrets"
    password_file_path = os.path.join(password_dir, "superuser_password.txt")
    
    logger.info("Starting superuser password change process")
    
    try:
        # Create secrets directory if it doesn't exist
        os.makedirs(password_dir, exist_ok=True)
        logger.debug(f"Ensured password directory exists at {password_dir}")

        # Check if the password file exists
        if os.path.exists(password_file_path):
            logger.info("Found existing password file")
            with open(password_file_path, "r") as f:
                stored_password = f.read().strip()
            if stored_password:
                # Connect to check if password needs updating
                admin_user = os.getenv("POSTGRES_USER", "postgres")
                admin_password = quote_plus(os.getenv("POSTGRES_PASSWORD", "defaultpassword"))
                db_host = os.getenv("POSTGRES_HOST", "localhost")
                db_port = os.getenv("POSTGRES_PORT", "5432")
                
                logger.debug(f"Attempting to connect to database at {db_host}:{db_port}")

                try:
                    # Try to connect with stored password
                    conn = psycopg2.connect(
                        dbname="postgres",
                        user=admin_user,
                        password=stored_password,
                        host=db_host,
                        port=db_port
                    )
                    conn.close()
                    logger.info("Successfully connected using existing password")
                    # Run migrations after successful connection
                    run_migrations()
                    return
                except psycopg2.OperationalError as e:
                    logger.warning(f"Connection failed with stored password: {e}")
                    # If connection fails with stored password, try with default
                    try:
                        conn = psycopg2.connect(
                            dbname="postgres",
                            user=admin_user,
                            password=admin_password,
                            host=db_host,
                            port=db_port
                        )
                        conn.autocommit = True
                        cursor = conn.cursor()
                        
                        # Update password to the stored one
                        logger.info("Updating database password to match stored password")
                        cursor.execute(
                            sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                                sql.Identifier(admin_user)
                            ), 
                            [stored_password]
                        )
                        
                        cursor.close()
                        conn.close()
                        logger.info("Successfully updated database password")
                        # Run migrations after password update
                        run_migrations()
                        return
                    except psycopg2.Error as e:
                        logger.error(f"Failed to update password: {e}", exc_info=True)
                        return

        # Generate new password if no valid stored password exists
        logger.info("Generating new password")
        db_password = generate_random_password()
        admin_user = os.getenv("POSTGRES_USER", "postgres")
        admin_password = quote_plus(os.getenv("POSTGRES_PASSWORD", "defaultpassword"))
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")

        try:
            # Connect to the PostgreSQL server
            logger.debug(f"Connecting to database to set new password")
            conn = psycopg2.connect(
                dbname="postgres",
                user=admin_user,
                password=admin_password,
                host=db_host,
                port=db_port
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Store the new password
            logger.debug("Writing new password to file")
            with open(password_file_path, "w") as f:
                f.write(db_password)

            # Change the superuser password
            logger.info("Setting new database password")
            cursor.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                    sql.Identifier(admin_user)
                ), 
                [db_password]
            )

            cursor.close()
            conn.close()
            logger.info("Successfully completed password change process")
            # Run migrations after setting up new password
            run_migrations()
            
        except Exception as e:
            logger.error(f"Critical error during password change: {e}", exc_info=True)
            raise
            
    except Exception as e:
        logger.error(f"Unexpected error in change_superuser_password: {e}", exc_info=True)
        raise

def run_migrations():
    """Run database migrations and ensure tables exist"""
    from sqlalchemy import create_engine, inspect
    from app.database.models import Base
    from app.database.connection import get_connection_string
    from alembic.config import Config
    from alembic import command
    import time
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Get database connection
            connection_string = get_connection_string()
            engine = create_engine(connection_string)
            
            # Check if tables exist
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # Create tables if they don't exist
            if not existing_tables:
                logger.info("No tables found. Creating database tables...")
                Base.metadata.create_all(engine)
                logger.info("Database tables created successfully")
            
            # Use the existing alembic.ini file for migrations
            alembic_cfg = Config("alembic.ini")
            
            # Run migrations to handle any schema changes
            command.upgrade(alembic_cfg, "head")
            
            logger.info("Database migrations completed successfully")
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Migration attempt {attempt + 1} failed: {str(e)}")
                time.sleep(retry_delay)
            else:
                logger.error("Failed to run migrations after multiple attempts", exc_info=True)
                return False
