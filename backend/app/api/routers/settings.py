from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.settings.app_settings import AppSettings

settings_router = r = APIRouter()

class AppSettingsModel(BaseModel):
    model_provider: str
    ollama_model: str
    openai_model: str
    anthropic_model: str
    groq_model: str
    gemini_model: str
    mistral_model: str
    azure_openai_model: str
    tgi_model: str
    embedding_model_provider: str
    ollama_embedding_model: str
    openai_embedding_model: str
    azure_openai_embedding_model: str
    gemini_embedding_model: str
    mistral_embedding_model: str
    fastembed_embedding_model: str
    embedding_dim: str
    top_k: int
    system_prompt: str
    custom_ollama_host: str
    tgi_host: str
    ollama_request_timeout: float
    tgi_request_timeout: float
    openai_api_key: str
    max_iterations: int
    files_tool_description: str

@r.get("")
async def get_settings() -> AppSettingsModel:
    """Get current application settings"""
    return AppSettingsModel(
        model_provider=AppSettings.model_provider,
        ollama_model=AppSettings.ollama_model,
        openai_model=AppSettings.openai_model,
        anthropic_model=AppSettings.anthropic_model,
        groq_model=AppSettings.groq_model,
        gemini_model=AppSettings.gemini_model,
        mistral_model=AppSettings.mistral_model,
        azure_openai_model=AppSettings.azure_openai_model,
        tgi_model=AppSettings.tgi_model,
        embedding_model_provider=AppSettings.embedding_model_provider,
        ollama_embedding_model=AppSettings.ollama_embedding_model,
        openai_embedding_model=AppSettings.openai_embedding_model,
        azure_openai_embedding_model=AppSettings.azure_openai_embedding_model,
        gemini_embedding_model=AppSettings.gemini_embedding_model,
        mistral_embedding_model=AppSettings.mistral_embedding_model,
        fastembed_embedding_model=AppSettings.fastembed_embedding_model,
        embedding_dim=AppSettings.embedding_dim,
        top_k=AppSettings.top_k,
        system_prompt=AppSettings.system_prompt,
        custom_ollama_host=AppSettings.custom_ollama_host,
        tgi_host=AppSettings.tgi_host,
        ollama_request_timeout=AppSettings.ollama_request_timeout,
        tgi_request_timeout=AppSettings.tgi_request_timeout,
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
            ollama_model=settings.ollama_model,
            openai_model=settings.openai_model,
            anthropic_model=settings.anthropic_model,
            groq_model=settings.groq_model,
            gemini_model=settings.gemini_model,
            mistral_model=settings.mistral_model,
            azure_openai_model=settings.azure_openai_model,
            tgi_model=settings.tgi_model,
            embedding_model_provider=settings.embedding_model_provider,
            ollama_embedding_model=settings.ollama_embedding_model,
            openai_embedding_model=settings.openai_embedding_model,
            azure_openai_embedding_model=settings.azure_openai_embedding_model,
            gemini_embedding_model=settings.gemini_embedding_model,
            mistral_embedding_model=settings.mistral_embedding_model,
            fastembed_embedding_model=settings.fastembed_embedding_model,
            embedding_dim=settings.embedding_dim,
            top_k=settings.top_k,
            system_prompt=settings.system_prompt,
            custom_ollama_host=settings.custom_ollama_host,
            tgi_host=settings.tgi_host,
            ollama_request_timeout=settings.ollama_request_timeout,
            tgi_request_timeout=settings.tgi_request_timeout,
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