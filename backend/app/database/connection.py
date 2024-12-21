import os
def get_connection_string() -> str:
    """Get the database connection string from environment variables"""
    user = "idapt-backend"
    # Get the database password from the password manager
    password = get_db_password()
    host = "idapt-postgres"
    port = "5432"
    db = "idapt-backend"
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

# Read the password from the postgres_backend_secrets file
def get_db_password():
    with open('/postgres_backend_secrets/IDAPT_BACKEND_PASSWORD', 'r') as file:
        return file.read().strip()