import os
from app.settings.models import *


def init_ollama_embedding(ollama_embed_settings: OllamaEmbedSettings):
    try:
        from llama_index.embeddings.ollama import OllamaEmbedding
    except ImportError:
        raise ImportError(
            "Ollama support is not installed. Please install it with `poetry add llama-index-llms-ollama` and `poetry add llama-index-embeddings-ollama`"
        )
    return OllamaEmbedding(
        base_url=ollama_embed_settings.host,
        model_name=ollama_embed_settings.model,
        embed_batch_size=2048
    )

def init_ollama_llm(ollama_llm_settings: OllamaLLMSettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.ollama.base import Ollama
    except ImportError:
        raise ImportError(
            "Ollama support is not installed. Please install it with `poetry add llama-index-llms-ollama`"
        )
    return Ollama(
        base_url=ollama_llm_settings.host,
        model=ollama_llm_settings.model,
        request_timeout=ollama_llm_settings.request_timeout,
        temperature=temperature,
        system_prompt=system_prompt
    )

def init_openai_embedding(openai_embed_settings: OpenAIEmbedSettings):
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
    except ImportError:
        raise ImportError(
            "OpenAI support is not installed. Please install it with `poetry add llama-index-llms-openai` and `poetry add llama-index-embeddings-openai`"
        )
    os.environ["OPENAI_API_KEY"] = openai_embed_settings.api_key
    return OpenAIEmbedding(
        model=openai_embed_settings.model,
        dimensions=int(openai_embed_settings.dimensions) if openai_embed_settings.dimensions is not None else None,
        embed_batch_size=2048
    )


def init_openai_llm(openai_llm_settings: OpenAILLMSettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI support is not installed. Please install it with `poetry add llama-index-llms-openai`"
        )
    os.environ["OPENAI_API_KEY"] = openai_llm_settings.api_key
    return OpenAI(
        model=openai_llm_settings.model,
        temperature=float(temperature),
        max_tokens=int(openai_llm_settings.max_tokens) if openai_llm_settings.max_tokens is not None else None,
        system_prompt=system_prompt
    )

def init_azure_openai_embedding(azure_embed_settings: AzureOpenAIEmbedSettings):
    try:
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
    except ImportError:
        raise ImportError(
            "Azure OpenAI support is not installed. Please install it with `poetry add llama-index-embeddings-azure-openai`"
        )
    
    azure_config = {
        "api_key": azure_embed_settings.api_key,
        "azure_endpoint": azure_embed_settings.endpoint,
        "api_version": azure_embed_settings.api_version,
    }

    return AzureOpenAIEmbedding(
        model=azure_embed_settings.model,
        dimensions=int(azure_embed_settings.dimensions) if azure_embed_settings.dimensions is not None else None,
        deployment_name=azure_embed_settings.deployment_name,
        embed_batch_size=2048,
        **azure_config,
    )

def init_azure_openai_llm(azure_llm_settings: AzureOpenAILLMSettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.azure_openai import AzureOpenAI
    except ImportError:
        raise ImportError(
            "Azure OpenAI support is not installed. Please install it with `poetry add llama-index-llms-azure-openai`"
        )
    
    azure_config = {
        "api_key": azure_llm_settings.api_key,
        "azure_endpoint": azure_llm_settings.endpoint,
        "api_version": azure_llm_settings.api_version,
    }
    
    return AzureOpenAI(
        model=azure_llm_settings.model,
        max_tokens=int(azure_llm_settings.max_tokens) if azure_llm_settings.max_tokens is not None else None,
        temperature=float(temperature),
        system_prompt=system_prompt,
        deployment_name=azure_llm_settings.deployment_name,
        **azure_config,
    )

def init_fastembed_embedding(fastembed_embed_settings: FastEmbedEmbedSettings):
    try:
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
    except ImportError:
        raise ImportError(
            "FastEmbed support is not installed. Please install it with `poetry add llama-index-embeddings-fastembed`"
        )

    return FastEmbedEmbedding(
        model_name=fastembed_embed_settings.model_name,
        embed_batch_size=2048
    )

def init_groq_llm(groq_llm_settings: GroqLLMSettings, system_prompt: str):
    try:
        from llama_index.llms.groq import Groq
    except ImportError:
        raise ImportError(
            "Groq support is not installed. Please install it with `poetry add llama-index-llms-groq`"
        )
    return Groq(
        model=groq_llm_settings.model,
        api_key=groq_llm_settings.api_key,
        system_prompt=system_prompt,
    )

def init_anthropic_llm(anthropic_llm_settings: AnthropicLLMSettings, system_prompt: str):
    try:
        from llama_index.llms.anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "Anthropic support is not installed. Please install it with `poetry add llama-index-llms-anthropic`"
        )

    return Anthropic(
        model=anthropic_llm_settings.model,
        api_key=anthropic_llm_settings.api_key,
        system_prompt=system_prompt,
    )

def init_gemini_embedding(gemini_embed_settings: GeminiEmbedSettings):
    try:
        from llama_index.embeddings.gemini import GeminiEmbedding
    except ImportError:
        raise ImportError(
            "Gemini support is not installed. Please install it with `poetry add llama-index-embeddings-gemini`"
        )
    return GeminiEmbedding(
        model_name=gemini_embed_settings.model,
        embed_batch_size=2048
    )

def init_gemini_llm(gemini_llm_settings: GeminiLLMSettings):
    try:
        from llama_index.llms.gemini import Gemini
    except ImportError:
        raise ImportError(
            "Gemini support is not installed. Please install it with `poetry add llama-index-llms-gemini`"
        )
    return Gemini(
        model=gemini_llm_settings.model,
        api_key=gemini_llm_settings.api_key,
    )

def init_mistral_embedding(mistral_embed_settings: MistralEmbedSettings):
    try:
        from llama_index.embeddings.mistralai import MistralAIEmbedding
    except ImportError:
        raise ImportError(
            "Mistral support is not installed. Please install it with `poetry add llama-index-embeddings-mistralai`"
        )
    return MistralAIEmbedding(
        model_name=mistral_embed_settings.model,
        embed_batch_size=2048
    )

def init_mistral_llm(mistral_llm_settings: MistralLLMSettings, system_prompt: str):
    try:
        from llama_index.llms.mistralai import MistralAI
    except ImportError:
        raise ImportError(
            "Mistral support is not installed. Please install it with `poetry add llama-index-llms-mistralai`"
        )
    return MistralAI(
        model=mistral_llm_settings.model,
        api_key=mistral_llm_settings.api_key,
        system_prompt=system_prompt,
    )

# TODO : Still need some work to work, works with openai-community/gpt2 but issues with llama3.1, seems to be a prompt formatting issue
def init_tgi_llm(tgi_llm_settings: TGILLMSettings, temperature: float, system_prompt: str):
    try:
        from llama_index.llms.text_generation_inference import TextGenerationInference
    except ImportError:
        raise ImportError(
            "Text Generation Inference support is not installed. Please install it with `poetry add llama-index-llms-text-generation-inference`"
        )
    return TextGenerationInference(
        model_url=tgi_llm_settings.llm_host,
        model_name=tgi_llm_settings.llm_model,
        timeout=tgi_llm_settings.llm_request_timeout,
        temperature=temperature,
        system_prompt=system_prompt,
    )
    
# TODO : Finish implementation of this if useful, also find how to manage dimensions with it.
def init_tei_embedding(tei_embed_settings: TEIEmbedSettings):
    try:
        from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
    except ImportError:
        raise ImportError(
            "Text Embeddings Inference support is not installed. Please install it with `poetry add llama-index-embeddings-text-embeddings-inference`"
        )
    return TextEmbeddingsInference(
        base_url=tei_embed_settings.embedding_host,
        model_name=tei_embed_settings.embedding_model,
        embed_batch_size=2048
    )


