from fastapi import APIRouter, HTTPException
from app.settings.manager import SettingsManager
from app.settings.models import AppSettings
from pydantic import ValidationError
from typing import Dict, Any

settings_router = APIRouter()

@settings_router.get("")
async def get_settings() -> AppSettings:
    """Get current application settings"""
    return SettingsManager.get_instance().settings

@settings_router.post("")
async def update_settings(settings: AppSettings):
    """Update application settings"""
    try:
        SettingsManager.get_instance().update(**settings.model_dump())
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
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to update settings",
                "error": str(e)
            }
        )