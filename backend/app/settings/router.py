from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.utils import get_file_manager_db_session, get_user_id
from app.settings.service import get_setting, update_setting, create_setting, delete_setting, get_all_settings, get_all_settings_with_schema_identifier
from app.settings.schemas import CreateSettingRequest, UpdateSettingRequest, SettingResponse
from app.settings.utils import get_settings_db_session
import logging

logger = logging.getLogger("uvicorn")

settings_router = r = APIRouter()

@r.post("/{identifier}")
async def create_setting_route(
    identifier: str,
    create_setting_request: CreateSettingRequest,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
) -> None:
    try:
        create_setting(settings_db_session, identifier, create_setting_request)
    except Exception as e:
        logger.error(f"Error creating setting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("", response_model=List[SettingResponse])
async def get_all_settings_route(
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
) -> List[SettingResponse]:
    try:
        return get_all_settings(settings_db_session)
    except Exception as e:
        logger.error(f"Error getting all settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@r.get("/schema/{schema_identifier}", response_model=List[SettingResponse])
async def get_all_settings_with_schema_identifier_route(
    schema_identifier: str,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
) -> List[SettingResponse]:
    try:
        return get_all_settings_with_schema_identifier(settings_db_session, schema_identifier)
    except Exception as e:
        logger.error(f"Error getting all settings with schema identifier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/{identifier}", response_model=SettingResponse)
async def get_setting_route(
    identifier: str,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
) -> SettingResponse:
    try:
        logger.info(f"Getting setting {identifier}")
        return get_setting(settings_db_session, identifier)
    except Exception as e:
        logger.error(f"Error getting setting {identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@r.patch("/{identifier}")
async def update_setting_route(
    identifier: str,
    update_setting_request: UpdateSettingRequest,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
) -> None:
    try:
        logger.info(f"Updating setting {identifier} with value: {update_setting_request}")
        update_setting(settings_db_session, identifier, update_setting_request)
    except ValueError as e:
        logger.error(f"Error updating setting {identifier}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating setting {identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@r.delete("/{identifier}")
async def delete_setting_route(
    identifier: str,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
) -> None:
    try:
        delete_setting(settings_db_session, identifier)
    except Exception as e:
        logger.error(f"Error deleting setting {identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
