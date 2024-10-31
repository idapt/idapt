import os
from urllib.parse import urlparse

def get_connection_string():
    
    pg_user = os.getenv("POSTGRES_USER")
    pg_host = os.getenv("POSTGRES_HOST")
    pg_port = os.getenv("POSTGRES_PORT")
    pg_database = os.getenv("POSTGRES_DB")

    # Retrieve the password from the file
    with open(os.getenv("POSTGRES_PASSWORD_PATH"), "r") as f:
        pg_password = f.read().strip()

    # Construct the connection string
    connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    
    return connection_string
