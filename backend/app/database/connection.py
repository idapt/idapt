import os
from urllib.parse import quote_plus

def get_connection_string():
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_database = os.getenv("POSTGRES_DB", "postgres")

    # Retrieve the password from the file
    password_path = os.getenv("POSTGRES_PASSWORD_PATH", "/backend/secrets/superuser_password.txt")
    try:
        with open(password_path, "r") as f:
            pg_password = f.read().strip()
    except FileNotFoundError:
        pg_password = os.getenv("POSTGRES_PASSWORD", "defaultpassword")
    
    # Single URL encode the password
    pg_password = quote_plus(pg_password)

    # Construct the connection string
    connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    return connection_string
