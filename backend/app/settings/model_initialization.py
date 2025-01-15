from app.settings.models import *
from app.settings.model_providers import *
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM

from sqlalchemy.orm import Session
from app.services.settings import get_setting
from app.settings.models import AppSettings

def init_llm(session: Session) -> BaseLLM:
    """Initialize LLM based on model provider setting"""
    app_setting : AppSettings = get_setting(session, "app")
    match app_setting.llm_model_provider:
        case "openai":
            openai_settings : OpenAISettings = get_setting(session, "openai")
            return init_openai_llm(openai_settings, app_setting.temperature, app_setting.system_prompt)
        #case "groq":
        #    return init_groq_llm(settings.llm.groq_model, settings.system_prompt)
        #case "text-generation-inference":
        #    return init_tgi_llm(settings.tgi, settings.temperature, settings.system_prompt)
        #case "anthropic":
        #    return init_anthropic_llm(settings.llm.anthropic_model, settings.system_prompt)
        #case "gemini":
        #    return init_gemini_llm(settings.llm.gemini_model, settings.system_prompt)
        #case "mistral":
        #    return init_mistral_llm(settings.llm.mistral_model, settings.system_prompt)
        #case "azure-openai":
        #    return init_azure_openai_llm(settings.llm.azure_openai_model, settings.system_prompt)
        case _:
            ollama_settings : OllamaSettings = get_setting(session, "ollama")
            return init_ollama_llm(ollama_settings, app_setting.temperature, app_setting.system_prompt)
        
def init_embedding_model(session: Session) -> BaseEmbedding:
    """Initialize embedding model based on embedding_model_provider setting"""
    app_setting : AppSettings = get_setting(session, "app")
    match app_setting.embedding_model_provider:
        case "openai":
            openai_settings : OpenAISettings = get_setting(session, "openai")
            return init_openai_embedding(openai_settings, app_setting.embedding_dim)
        #case "azure-openai":
        #    return init_azure_openai_embedding(settings.embedding.azure_openai_embedding_model)
        #case "gemini":
        #    return init_gemini_embedding(settings.embedding.gemini_embedding_model)
        #case "mistral":
        #    return init_mistral_embedding(settings.embedding.mistral_embedding_model)
        #case "fastembed":
        #    return init_fastembed_embedding(settings.embedding.fastembed_embedding_model)
        #case "text-embeddings-inference":
        #    return init_tei_embedding(settings.tei, settings.embedding_dim)
        case _:
            ollama_settings : OllamaSettings = get_setting(session, "ollama")
            return init_ollama_embedding(ollama_settings)