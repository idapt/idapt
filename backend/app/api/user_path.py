from pathlib import Path
from typing import Optional

def get_user_data_dir(user_id: Optional[str] = None) -> str:
    """Get the data directory for a specific user"""
    if not user_id:
        raise ValueError("User ID is required")
    return str(Path("/data", user_id))

def get_user_app_data_dir(user_id: Optional[str] = None) -> str:
    """Get the app data directory for a specific user"""
    if not user_id:
        raise ValueError("User ID is required")
    return str(Path("/data", user_id, ".idapt"))