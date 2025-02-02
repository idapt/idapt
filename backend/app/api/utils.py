from fastapi import Header, Query, HTTPException
from typing import Optional
import logging

logger = logging.getLogger("uvicorn")

async def get_user_id(
    x_user_id: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None)
) -> str:
    """Get user ID from header or query parameter"""
    if x_user_id:
        return x_user_id
    if user_id:
        return user_id
    raise HTTPException(status_code=401, detail="User ID is required (either in X-User-Id header or user_id query parameter)") 