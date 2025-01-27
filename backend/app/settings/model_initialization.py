import json
from app.settings.schemas import *
from app.settings.model_providers import *
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM

def init_llm(llm_model_provider: str, llm_setting_value_json: str, app_setting_value_json: str) -> BaseLLM:
    """Initialize LLM based on model provider setting"""
    # Get the app settings
    app_settings : AppSettings = AppSettings.model_validate_json(app_setting_value_json)
    # Convert to corres pydantic model
    match llm_model_provider:
        case "openai_llm":
            openai_llm_settings : OpenAILLMSettings = OpenAILLMSettings.model_validate_json(llm_setting_value_json)
            return init_openai_llm(openai_llm_settings, app_settings.temperature, app_settings.system_prompt)
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
            ollama_llm_settings : OllamaLLMSettings = OllamaLLMSettings.model_validate_json(llm_setting_value_json)
            return init_ollama_llm(ollama_llm_settings, app_settings.temperature, app_settings.system_prompt)
        
def init_embedding_model(embedding_model_provider: str, embedding_settings_json: str) -> BaseEmbedding:
    """Initialize embedding model based on embedding_model_provider setting"""
    match embedding_model_provider:
        case "openai_embed":
            openai_settings : OpenAIEmbedSettings = OpenAIEmbedSettings.model_validate_json(embedding_settings_json)
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
            ollama_embed_settings : OllamaEmbedSettings = OllamaEmbedSettings.model_validate_json(embedding_settings_json)
            return init_ollama_embedding(ollama_embed_settings)
        case _:
            raise ValueError(f"Unknown embedding model provider: {embedding_model_provider}")
