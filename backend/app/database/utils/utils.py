from app.api.user_path import get_user_db_path

def get_db_path(user_id: str) -> str:
    """Get the database path"""
    return get_user_db_path(user_id)