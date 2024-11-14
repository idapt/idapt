import os
from typing import Dict

from llama_index.core.settings import Settings

from app.settings.app_settings import AppSettings


def update_llama_index_llm_and_embed_models_from_app_settings():
    model_provider = AppSettings.model_provider
    match model_provider:
        case "openai":
            init_openai()
        case "groq":
            init_groq()
        case "ollama":
            init_ollama()
        case "anthropic":
            init_anthropic()
        case "gemini":
            init_gemini()
        case "mistral":
            init_mistral()
        case "azure-openai":
            init_azure_openai()
        case "t-systems":
            from .llmhub import init_llmhub

            init_llmhub()
        case _:
            raise ValueError(f"Invalid model provider: {model_provider}")

    Settings.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
    Settings.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "20"))


def init_ollama():
    try:
        from llama_index.embeddings.ollama import OllamaEmbedding
        from llama_index.llms.ollama.base import DEFAULT_REQUEST_TIMEOUT, Ollama
    except ImportError:
        raise ImportError(
            "Ollama support is not installed. Please install it with `poetry add llama-index-llms-ollama` and `poetry add llama-index-embeddings-ollama`"
        )

    base_url = "http://" + os.getenv("OLLAMA_HOST", "ollama") + ":" + os.getenv("OLLAMA_PORT", "11434")
    request_timeout = float(
        os.getenv("OLLAMA_REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT)
    )
    Settings.embed_model = OllamaEmbedding(
        base_url=base_url,
        model_name=AppSettings.embedding_model,
    )
    Settings.llm = Ollama(
        base_url=base_url, model=AppSettings.model, request_timeout=request_timeout
    )


def init_openai():
    from llama_index.core.constants import DEFAULT_TEMPERATURE
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI

    max_tokens = os.getenv("LLM_MAX_TOKENS")
    Settings.llm = OpenAI(
        model=AppSettings.model,
        temperature=float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
        max_tokens=int(max_tokens) if max_tokens is not None else None,
    )

    dimensions = AppSettings.embedding_dim
    Settings.embed_model = OpenAIEmbedding(
        model=AppSettings.embedding_model,
        dimensions=int(dimensions) if dimensions is not None else None,
    )


def init_azure_openai():
    from llama_index.core.constants import DEFAULT_TEMPERATURE

    try:
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        from llama_index.llms.azure_openai import AzureOpenAI
    except ImportError:
        raise ImportError(
            "Azure OpenAI support is not installed. Please install it with `poetry add llama-index-llms-azure-openai` and `poetry add llama-index-embeddings-azure-openai`"
        )

    llm_deployment = os.environ["AZURE_OPENAI_LLM_DEPLOYMENT"]
    embedding_deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    temperature = os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)
    dimensions = AppSettings.embedding_dim

    azure_config = {
        "api_key": os.environ["AZURE_OPENAI_API_KEY"],
        "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION")
        or os.getenv("OPENAI_API_VERSION"),
    }

    Settings.llm = AzureOpenAI(
        model=AppSettings.model,
        max_tokens=int(max_tokens) if max_tokens is not None else None,
        temperature=float(temperature),
        deployment_name=llm_deployment,
        **azure_config,
    )

    Settings.embed_model = AzureOpenAIEmbedding(
        model=AppSettings.embedding_model,
        dimensions=int(dimensions) if dimensions is not None else None,
        deployment_name=embedding_deployment,
        **azure_config,
    )


def init_fastembed():
    try:
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
    except ImportError:
        raise ImportError(
            "FastEmbed support is not installed. Please install it with `poetry add llama-index-embeddings-fastembed`"
        )

    embed_model_map: Dict[str, str] = {
        # Small and multilingual
        "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
        # Large and multilingual
        "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    }

    embedding_model = AppSettings.embedding_model
    if embedding_model is None:
        raise ValueError("EMBEDDING_MODEL environment variable is not set")

    # This will download the model automatically if it is not already downloaded
    Settings.embed_model = FastEmbedEmbedding(
        model_name=embed_model_map[embedding_model]
    )


def init_groq():
    try:
        from llama_index.llms.groq import Groq
    except ImportError:
        raise ImportError(
            "Groq support is not installed. Please install it with `poetry add llama-index-llms-groq`"
        )

    Settings.llm = Groq(model=AppSettings.model)
    # Groq does not provide embeddings, so we use FastEmbed instead
    init_fastembed()


def init_anthropic():
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

    Settings.llm = Anthropic(model=model_map[AppSettings.model])
    # Anthropic does not provide embeddings, so we use FastEmbed instead
    init_fastembed()


def init_gemini():
    try:
        from llama_index.embeddings.gemini import GeminiEmbedding
        from llama_index.llms.gemini import Gemini
    except ImportError:
        raise ImportError(
            "Gemini support is not installed. Please install it with `poetry add llama-index-llms-gemini` and `poetry add llama-index-embeddings-gemini`"
        )

    model_name = f"models/{AppSettings.model}"
    embed_model_name = f"models/{AppSettings.embedding_model}"

    Settings.llm = Gemini(model=model_name)
    Settings.embed_model = GeminiEmbedding(model_name=embed_model_name)


def init_mistral():
    from llama_index.embeddings.mistralai import MistralAIEmbedding
    from llama_index.llms.mistralai import MistralAI

    Settings.llm = MistralAI(model=AppSettings.model)
    Settings.embed_model = MistralAIEmbedding(model_name=AppSettings.embedding_model)