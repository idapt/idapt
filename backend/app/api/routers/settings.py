from fastapi import APIRouter, HTTPException, Depends
from app.settings.manager import get_app_settings, save_app_settings
from app.settings.models import AppSettings
from pydantic import ValidationError
import logging

logger = logging.getLogger("uvicorn")

settings_router = r = APIRouter()

@r.get("")
async def get_settings_route() -> AppSettings:
    """Get current application settings"""
    logger.info(f"Getting application settings")
    return get_app_settings()

@r.post("")
async def update_settings_route(
    new_app_settings: AppSettings,
):
    """Update application settings"""
    try:
        logger.info(f"Updating application settings")
        save_app_settings(new_app_settings)
        return {"status": "success"}
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{field_path}: {error['msg']}")
        
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid settings provided",
                "errors": errors
            }
        )
    except Exception as e:
        logger.error(f"Error in update_settings_route: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to update settings",
                "error": str(e)
            }
        )