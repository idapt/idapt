from app.user.user_path import get_user_db_path

def get_db_path(user_id: str) -> str:
    """Get the database path"""
    return get_user_db_path(user_id)

def get_connection_string(user_id: str) -> str:
    """Get the database connection string for SQLite"""
    return f"sqlite:///{get_db_path(user_id)}"