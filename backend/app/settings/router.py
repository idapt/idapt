from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.utils import get_file_manager_db_session, get_user_id
from app.settings.service import get_setting, update_setting
from typing import Dict, Any
import logging
import json

logger = logging.getLogger("uvicorn")

settings_router = r = APIRouter()

@r.get("/{identifier}")
async def get_setting_route(
    identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
):
    try:
        logger.info(f"Getting setting {identifier}")
        return get_setting(session, identifier)
    except Exception as e:
        logger.error(f"Error getting setting {identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.post("/{identifier}")
async def update_setting_route(
    identifier: str,
    json_setting_object: Dict[str, Any],
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
):
    try:
        logger.info(f"Updating setting {identifier} with value: {json_setting_object}")
        if "json_setting_object_str" in json_setting_object:
            # Extract the inner JSON string and parse it
            inner_json = json.loads(json_setting_object["json_setting_object_str"])
            return update_setting(session, identifier, inner_json)
        return update_setting(session, identifier, json_setting_object)
    except Exception as e:
        logger.error(f"Error updating setting {identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))