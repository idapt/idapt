
def get_db_path() -> str:
    """Get the database path"""
    return "/data/.idapt/db/idapt.db"

def get_connection_string() -> str:
    """Get the database connection string for SQLite"""
    return f"sqlite:///{get_db_path()}"
