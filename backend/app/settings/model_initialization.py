from app.settings.manager import AppSettingsManager
from app.settings.models import *
from app.settings.model_providers import *

def init_llm(settings: AppSettings):
    """Initialize LLM based on model provider setting"""
    match settings.llm_model_provider:
        case "openai":
            return init_openai_llm(settings.openai, settings.temperature, settings.system_prompt)
        #case "groq":
        #    return init_groq_llm(settings.llm.groq_model, settings.system_prompt)
        case "custom_ollama":
            return init_ollama_llm(settings.custom_ollama, settings.temperature, settings.system_prompt)
        case "text-generation-inference":
            return init_tgi_llm(settings.tgi, settings.temperature, settings.system_prompt)
        #case "anthropic":
        #    return init_anthropic_llm(settings.llm.anthropic_model, settings.system_prompt)
        #case "gemini":
        #    return init_gemini_llm(settings.llm.gemini_model, settings.system_prompt)
        #case "mistral":
        #    return init_mistral_llm(settings.llm.mistral_model, settings.system_prompt)
        #case "azure-openai":
        #    return init_azure_openai_llm(settings.llm.azure_openai_model, settings.system_prompt)
        case _:
            return init_ollama_llm(settings.integrated_ollama, settings.temperature, settings.system_prompt)
        
def init_embedding_model(settings: AppSettings):
    """Initialize embedding model based on embedding_model_provider setting"""
    match settings.embedding_model_provider:
        case "openai":
            return init_openai_embedding(settings.openai, settings.embedding_dim)
        case "custom_ollama":
            return init_ollama_embedding(settings.custom_ollama)
        #case "azure-openai":
        #    return init_azure_openai_embedding(settings.embedding.azure_openai_embedding_model)
        #case "gemini":
        #    return init_gemini_embedding(settings.embedding.gemini_embedding_model)
        #case "mistral":
        #    return init_mistral_embedding(settings.embedding.mistral_embedding_model)
        #case "fastembed":
        #    return init_fastembed_embedding(settings.embedding.fastembed_embedding_model)
        case "text-embeddings-inference":
            return init_tei_embedding(settings.tei, settings.embedding_dim)
        case _:
            return init_ollama_embedding(settings.integrated_ollama)
