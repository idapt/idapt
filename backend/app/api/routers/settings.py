from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.settings.app_settings import AppSettings

settings_router = r = APIRouter()

class AppSettingsModel(BaseModel):
    model_provider: str
    model: str
    embedding_model: str
    embedding_dim: str
    top_k: int
    system_prompt: str

@r.get("")
async def get_settings() -> AppSettingsModel:
    """Get current application settings"""
    return AppSettingsModel(
        model_provider=AppSettings.model_provider,
        model=AppSettings.model,
        embedding_model=AppSettings.embedding_model,
        embedding_dim=AppSettings.embedding_dim,
        top_k=AppSettings.top_k,
        system_prompt=AppSettings.system_prompt
    )

@r.post("")
async def update_settings(settings: AppSettingsModel):
    """Update application settings"""
    try:
        AppSettings.update(
            model_provider=settings.model_provider,
            model=settings.model,
            embedding_model=settings.embedding_model,
            embedding_dim=settings.embedding_dim,
            top_k=settings.top_k,
            system_prompt=settings.system_prompt
        )
        
        # Update llama index settings after changing model settings
        from app.settings.llama_index_settings import update_llama_index_llm_and_embed_models_from_app_settings
        update_llama_index_llm_and_embed_models_from_app_settings()
        
        return {"status": "success"}
    except ImportError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        ) 