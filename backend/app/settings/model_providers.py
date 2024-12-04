from typing import Dict
import os
from llama_index.core.settings import Settings
from llama_index.core.constants import DEFAULT_TEMPERATURE
from app.settings.app_settings import AppSettings

# Base URLs
INTEGRATED_OLLAMA_URL = "http://idapt-nginx:3030/integrated-ollama"
CUSTOM_OLLAMA_URL = "http://idapt-nginx:3030/local-ollama"

def _get_ollama_imports():
    """Helper function to import Ollama-related modules"""
    try:
        from llama_index.embeddings.ollama import OllamaEmbedding
        from llama_index.llms.ollama.base import Ollama
        return OllamaEmbedding, Ollama
    except ImportError:
        raise ImportError(
            "Ollama support is not installed. Please install it with `poetry add llama-index-llms-ollama` and `poetry add llama-index-embeddings-ollama`"
        )

def init_integrated_ollama_embedding():
    OllamaEmbedding, _ = _get_ollama_imports()
    return OllamaEmbedding(
        base_url=INTEGRATED_OLLAMA_URL,
        model_name=AppSettings.embedding_model,
    )

def init_custom_ollama_embedding():
    OllamaEmbedding, _ = _get_ollama_imports()
    return OllamaEmbedding(
        base_url=CUSTOM_OLLAMA_URL,
        model_name=AppSettings.embedding_model,
    )

def init_integrated_ollama_llm():
    _, Ollama = _get_ollama_imports()
    return Ollama(
        base_url=INTEGRATED_OLLAMA_URL,
        model=AppSettings.model,
        request_timeout=AppSettings.ollama_request_timeout,
        system_prompt=AppSettings.system_prompt
    )

def init_custom_ollama_llm():
    _, Ollama = _get_ollama_imports()
    return Ollama(
        base_url=CUSTOM_OLLAMA_URL,
        model=AppSettings.model,
        request_timeout=AppSettings.ollama_request_timeout,
        system_prompt=AppSettings.system_prompt
    )

def _get_openai_imports():
    """Helper function to import OpenAI-related modules"""
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        return OpenAIEmbedding, OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI support is not installed. Please install it with `poetry add llama-index-llms-openai`"
        )

def init_openai_embedding():
    OpenAIEmbedding, _ = _get_openai_imports()
    dimensions = AppSettings.embedding_dim
    os.environ["OPENAI_API_KEY"] = AppSettings.openai_api_key
    return OpenAIEmbedding(
        model=AppSettings.embedding_model,
        dimensions=int(dimensions) if dimensions is not None else None,
    )

def init_openai_llm():
    _, OpenAI = _get_openai_imports()
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    os.environ["OPENAI_API_KEY"] = AppSettings.openai_api_key
    return OpenAI(
        model=AppSettings.model,
        temperature=float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
        max_tokens=int(max_tokens) if max_tokens is not None else None,
        system_prompt=AppSettings.system_prompt
    )

def _get_azure_openai_imports():
    """Helper function to import Azure OpenAI-related modules"""
    try:
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        from llama_index.llms.azure_openai import AzureOpenAI
        return AzureOpenAIEmbedding, AzureOpenAI
    except ImportError:
        raise ImportError(
            "Azure OpenAI support is not installed. Please install it with `poetry add llama-index-llms-azure-openai` and `poetry add llama-index-embeddings-azure-openai`"
        )

def _get_azure_config():
    """Helper function to get Azure configuration"""
    return {
        "api_key": os.environ["AZURE_OPENAI_API_KEY"],
        "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION") or os.getenv("OPENAI_API_VERSION"),
    }

def init_azure_openai_embedding():
    AzureOpenAIEmbedding, _ = _get_azure_openai_imports()
    embedding_deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    dimensions = AppSettings.embedding_dim
    
    return AzureOpenAIEmbedding(
        model=AppSettings.embedding_model,
        dimensions=int(dimensions) if dimensions is not None else None,
        deployment_name=embedding_deployment,
        **_get_azure_config(),
    )

def init_azure_openai_llm():
    _, AzureOpenAI = _get_azure_openai_imports()
    llm_deployment = os.environ["AZURE_OPENAI_LLM_DEPLOYMENT"]
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    temperature = os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)
    
    return AzureOpenAI(
        model=AppSettings.model,
        max_tokens=int(max_tokens) if max_tokens is not None else None,
        temperature=float(temperature),
        system_prompt=AppSettings.system_prompt,
        deployment_name=llm_deployment,
        **_get_azure_config(),
    )

def init_fastembed_embedding():
    try:
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
    except ImportError:
        raise ImportError(
            "FastEmbed support is not installed. Please install it with `poetry add llama-index-embeddings-fastembed`"
        )

    embed_model_map: Dict[str, str] = {
        "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
        "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    }

    embedding_model = AppSettings.embedding_model
    if embedding_model is None:
        raise ValueError("embedding_model is not set")

    return FastEmbedEmbedding(model_name=embed_model_map[embedding_model])

def init_groq_llm():
    try:
        from llama_index.llms.groq import Groq
    except ImportError:
        raise ImportError(
            "Groq support is not installed. Please install it with `poetry add llama-index-llms-groq`"
        )
    return Groq(model=AppSettings.model, system_prompt=AppSettings.system_prompt)

def init_anthropic_llm():
    try:
        from llama_index.llms.anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "Anthropic support is not installed. Please install it with `poetry add llama-index-llms-anthropic`"
        )

    model_map: Dict[str, str] = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-2.1": "claude-2.1",
        "claude-instant-1.2": "claude-instant-1.2",
    }

    return Anthropic(model=model_map[AppSettings.model], system_prompt=AppSettings.system_prompt)

def _get_gemini_imports():
    """Helper function to import Gemini-related modules"""
    try:
        from llama_index.embeddings.gemini import GeminiEmbedding
        from llama_index.llms.gemini import Gemini
        return GeminiEmbedding, Gemini
    except ImportError:
        raise ImportError(
            "Gemini support is not installed. Please install it with `poetry add llama-index-llms-gemini` and `poetry add llama-index-embeddings-gemini`"
        )

def init_gemini_embedding():
    GeminiEmbedding, _ = _get_gemini_imports()
    embed_model_name = f"models/{AppSettings.embedding_model}"
    return GeminiEmbedding(model_name=embed_model_name)

def init_gemini_llm():
    _, Gemini = _get_gemini_imports()
    model_name = f"models/{AppSettings.model}"
    return Gemini(model=model_name)

def _get_mistral_imports():
    """Helper function to import Mistral-related modules"""
    try:
        from llama_index.embeddings.mistralai import MistralAIEmbedding
        from llama_index.llms.mistralai import MistralAI
        return MistralAIEmbedding, MistralAI
    except ImportError:
        raise ImportError(
            "Mistral support is not installed. Please install it with `poetry add llama-index-llms-mistralai` and `poetry add llama-index-embeddings-mistralai`"
        )

def init_mistral_embedding():
    MistralAIEmbedding, _ = _get_mistral_imports()
    return MistralAIEmbedding(model_name=AppSettings.embedding_model)

def init_mistral_llm():
    _, MistralAI = _get_mistral_imports()
    return MistralAI(model=AppSettings.model, system_prompt=AppSettings.system_prompt)