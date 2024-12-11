import os
from app.settings.models import *


def init_ollama_embedding(ollama_settings: OllamaSettings):
    try:
        from llama_index.embeddings.ollama import OllamaEmbedding
    except ImportError:
        raise ImportError(
            "Ollama support is not installed. Please install it with `poetry add llama-index-llms-ollama` and `poetry add llama-index-embeddings-ollama`"
        )
    return OllamaEmbedding(
        base_url=ollama_settings.llm_host,
        model_name=ollama_settings.embedding_model,
        embed_batch_size=2048
    )

def init_ollama_llm(ollama_settings: OllamaSettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.ollama.base import Ollama
    except ImportError:
        raise ImportError(
            "Ollama support is not installed. Please install it with `poetry add llama-index-llms-ollama`"
        )
    return Ollama(
        base_url=ollama_settings.llm_host,
        model=ollama_settings.llm_model,
        request_timeout=ollama_settings.llm_request_timeout,
        temperature=temperature,
        system_prompt=system_prompt
    )

def init_openai_embedding(openai_settings: OpenAISettings):
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
    except ImportError:
        raise ImportError(
            "OpenAI support is not installed. Please install it with `poetry add llama-index-llms-openai` and `poetry add llama-index-embeddings-openai`"
        )
    os.environ["OPENAI_API_KEY"] = openai_settings.api_key
    return OpenAIEmbedding(
        model=openai_settings.embedding_model,
        dimensions=int(openai_settings.dimensions) if openai_settings.dimensions is not None else None,
        embed_batch_size=2048
    )


def init_openai_llm(openai_settings: OpenAISettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI support is not installed. Please install it with `poetry add llama-index-llms-openai`"
        )
    os.environ["OPENAI_API_KEY"] = openai_settings.api_key
    return OpenAI(
        model=openai_settings.llm_model,
        temperature=float(temperature),
        max_tokens=int(openai_settings.max_tokens) if openai_settings.max_tokens is not None else None,
        system_prompt=system_prompt
    )

def init_azure_openai_embedding(azure_settings: AzureOpenAISettings):
    try:
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
    except ImportError:
        raise ImportError(
            "Azure OpenAI support is not installed. Please install it with `poetry add llama-index-embeddings-azure-openai`"
        )
    
    azure_config = {
        "api_key": azure_settings.api_key,
        "azure_endpoint": azure_settings.endpoint,
        "api_version": azure_settings.api_version,
    }

    return AzureOpenAIEmbedding(
        model=azure_settings.llm_model,
        dimensions=int(azure_settings.dimensions) if azure_settings.dimensions is not None else None,
        deployment_name=azure_settings.deployment_name,
        embed_batch_size=2048,
        **azure_config,
    )

def init_azure_openai_llm(azure_settings: AzureOpenAISettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.azure_openai import AzureOpenAI
    except ImportError:
        raise ImportError(
            "Azure OpenAI support is not installed. Please install it with `poetry add llama-index-llms-azure-openai`"
        )
    
    azure_config = {
        "api_key": azure_settings.api_key,
        "azure_endpoint": azure_settings.endpoint,
        "api_version": azure_settings.api_version,
    }
    
    return AzureOpenAI(
        model=azure_settings.llm_model,
        max_tokens=int(azure_settings.max_tokens) if azure_settings.max_tokens is not None else None,
        temperature=float(temperature),
        system_prompt=system_prompt,
        deployment_name=azure_settings.deployment_name,
        **azure_config,
    )

def init_fastembed_embedding(fastembed_settings: FastEmbedSettings):
    try:
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
    except ImportError:
        raise ImportError(
            "FastEmbed support is not installed. Please install it with `poetry add llama-index-embeddings-fastembed`"
        )

    return FastEmbedEmbedding(
        model_name=fastembed_settings.model_name,
        embed_batch_size=2048
    )

def init_groq_llm(groq_settings: GroqSettings, system_prompt: str):
    try:
        from llama_index.llms.groq import Groq
    except ImportError:
        raise ImportError(
            "Groq support is not installed. Please install it with `poetry add llama-index-llms-groq`"
        )
    return Groq(
        model=groq_settings.llm_model,
        api_key=groq_settings.api_key,
        system_prompt=system_prompt,
    )

def init_anthropic_llm(anthropic_settings: AnthropicSettings, system_prompt: str):
    try:
        from llama_index.llms.anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "Anthropic support is not installed. Please install it with `poetry add llama-index-llms-anthropic`"
        )

    return Anthropic(
        model=anthropic_settings.llm_model,
        api_key=anthropic_settings.api_key,
        system_prompt=system_prompt,
    )

def init_gemini_embedding(gemini_settings: GeminiSettings):
    try:
        from llama_index.embeddings.gemini import GeminiEmbedding
    except ImportError:
        raise ImportError(
            "Gemini support is not installed. Please install it with `poetry add llama-index-embeddings-gemini`"
        )
    return GeminiEmbedding(
        model_name=gemini_settings.llm_model,
        embed_batch_size=2048
    )

def init_gemini_llm(gemini_settings: GeminiSettings):
    try:
        from llama_index.llms.gemini import Gemini
    except ImportError:
        raise ImportError(
            "Gemini support is not installed. Please install it with `poetry add llama-index-llms-gemini`"
        )
    return Gemini(
        model=gemini_settings.llm_model,
        api_key=gemini_settings.api_key,
    )

def init_mistral_embedding(mistral_settings: MistralSettings):
    try:
        from llama_index.embeddings.mistralai import MistralAIEmbedding
    except ImportError:
        raise ImportError(
            "Mistral support is not installed. Please install it with `poetry add llama-index-embeddings-mistralai`"
        )
    return MistralAIEmbedding(
        model_name=mistral_settings.llm_model,
        embed_batch_size=2048
    )

def init_mistral_llm(mistral_settings: MistralSettings, system_prompt: str):
    try:
        from llama_index.llms.mistralai import MistralAI
    except ImportError:
        raise ImportError(
            "Mistral support is not installed. Please install it with `poetry add llama-index-llms-mistralai`"
        )
    return MistralAI(
        model=mistral_settings.llm_model,
        api_key=mistral_settings.api_key,
        system_prompt=system_prompt,
    )

# TODO : Still need some work to work, works with openai-community/gpt2 but issues with llama3.1, seems to be a prompt formatting issue
def init_tgi_llm(tgi_settings: TGISettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.text_generation_inference import TextGenerationInference
    except ImportError:
        raise ImportError(
            "Text Generation Inference support is not installed. Please install it with `poetry add llama-index-llms-text-generation-inference`"
        )
    return TextGenerationInference(
        model_url=tgi_settings.llm_host,
        model_name=tgi_settings.llm_model,
        timeout=tgi_settings.llm_request_timeout,
        temperature=temperature,
        system_prompt=system_prompt,
    )
    
# TODO : Finish implementation of this if useful, also find how to manage dimensions with it.
def init_tei_embedding(tei_settings: TEISettings):
    try:
        from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
    except ImportError:
        raise ImportError(
            "Text Embeddings Inference support is not installed. Please install it with `poetry add llama-index-embeddings-text-embeddings-inference`"
        )
    return TextEmbeddingsInference(
        base_url=tei_settings.embedding_host,
        model_name=tei_settings.embedding_model,
        embed_batch_size=2048
    )


