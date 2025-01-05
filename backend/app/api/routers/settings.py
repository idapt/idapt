from fastapi import APIRouter, HTTPException, Depends
from app.settings.manager import AppSettingsManager
from app.settings.models import AppSettings
from pydantic import ValidationError

settings_router = r = APIRouter()

def get_app_settings_manager():
    return AppSettingsManager.get_instance()

@r.get("")
async def get_settings_route(
    app_settings_manager: AppSettingsManager = Depends(get_app_settings_manager)
) -> AppSettings:
    """Get current application settings"""
    return app_settings_manager.settings

@r.post("")
async def update_settings_route(
    settings: AppSettings,
    app_settings_manager: AppSettingsManager = Depends(get_app_settings_manager)
):
    """Update application settings"""
    try:
        app_settings_manager.update(**settings.model_dump())
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