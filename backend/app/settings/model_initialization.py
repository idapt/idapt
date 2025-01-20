import json
from app.settings.schemas import *
from app.settings.model_providers import *
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM

from sqlalchemy.orm import Session
from app.settings.service import get_setting
from app.settings.schemas import AppSettings

def init_llm(session: Session) -> BaseLLM:
    """Initialize LLM based on model provider setting"""
    app_setting : AppSettings = get_setting(session, "app")
    match app_setting.llm_model_provider:
        case "openai_llm":
            openai_llm_settings : OpenAILLMSettings = get_setting(session, "openai_llm")
            return init_openai_llm(openai_llm_settings, app_setting.temperature, app_setting.system_prompt)
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
            ollama_llm_settings : OllamaLLMSettings = get_setting(session, "ollama_llm")
            return init_ollama_llm(ollama_llm_settings, app_setting.temperature, app_setting.system_prompt)
        
def init_embedding_model(embedding_model_provider: str, embedding_settings_json: str) -> BaseEmbedding:
    """Initialize embedding model based on embedding_model_provider setting"""
    embedding_settings = json.loads(embedding_settings_json)
    match embedding_model_provider:
        case "openai_embed":
            openai_settings : OpenAIEmbedSettings = OpenAIEmbedSettings(**embedding_settings)
            return init_openai_embedding(openai_settings)
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
        case "ollama_embed":
            ollama_embed_settings : OllamaEmbedSettings = OllamaEmbedSettings(**embedding_settings)
            return init_ollama_embedding(ollama_embed_settings)
        case _:
            raise ValueError(f"Unknown embedding model provider: {embedding_model_provider}")
