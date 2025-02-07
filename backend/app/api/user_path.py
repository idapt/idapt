from pathlib import Path
from typing import Optional

def get_user_data_dir(user_uuid: Optional[str] = None) -> str:
    """Get the data directory for a specific user"""
    if not user_uuid:
        raise ValueError("User ID is required")
    return str(Path("/data", user_uuid))

def get_user_app_data_dir(user_uuid: Optional[str] = None) -> str:
    """Get the app data directory for a specific user"""
    if not user_uuid:
        raise ValueError("User ID is required")
    return str(Path("/data", user_uuid, ".idapt"))