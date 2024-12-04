from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.settings.app_settings import AppSettings

settings_router = r = APIRouter()

class AppSettingsModel(BaseModel):
    model_provider: str
    model: str
    embedding_model_provider: str
    embedding_model: str
    embedding_dim: str
    top_k: int
    system_prompt: str
    custom_ollama_host: str
    ollama_request_timeout: float
    openai_api_key: str
    max_iterations: int
    files_tool_description: str

@r.get("")
async def get_settings() -> AppSettingsModel:
    """Get current application settings"""
    return AppSettingsModel(
        model_provider=AppSettings.model_provider,
        model=AppSettings.model,
        embedding_model_provider=AppSettings.embedding_model_provider,
        embedding_model=AppSettings.embedding_model,
        embedding_dim=AppSettings.embedding_dim,
        top_k=AppSettings.top_k,
        system_prompt=AppSettings.system_prompt,
        custom_ollama_host=AppSettings.custom_ollama_host,
        ollama_request_timeout=AppSettings.ollama_request_timeout,
        openai_api_key=AppSettings.openai_api_key,
        max_iterations=AppSettings.max_iterations,
        files_tool_description=AppSettings.files_tool_description
    )

@r.post("")
async def update_settings(settings: AppSettingsModel):
    """Update application settings"""
    try:
        AppSettings.update(
            model_provider=settings.model_provider,
            model=settings.model,
            embedding_model_provider=settings.embedding_model_provider,
            embedding_model=settings.embedding_model,
            embedding_dim=settings.embedding_dim,
            top_k=settings.top_k,
            system_prompt=settings.system_prompt,
            custom_ollama_host=settings.custom_ollama_host,
            ollama_request_timeout=settings.ollama_request_timeout,
            openai_api_key=settings.openai_api_key,
            max_iterations=settings.max_iterations,
            files_tool_description=settings.files_tool_description
        )

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