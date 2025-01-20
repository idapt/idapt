from pydantic import BaseModel
from typing import Literal, Optional

class SettingBase(BaseModel):
    identifier: str
    display_name: str
    description: Optional[str] = None

# LLM Settings
class OllamaLLMSettings(SettingBase):
    identifier: str = "ollama_llm"
    display_name: str = "Ollama LLM"
    description: str = "Ollama LLM provider settings"
    model: str = "llama3.1:8b"
    host: str = "http://host.docker.internal:11434"
    request_timeout: float = 300

class OllamaEmbedSettings(SettingBase):
    identifier: str = "ollama_embed"
    display_name: str = "Ollama Embeddings"
    description: str = "Ollama embedding provider settings"
    model: str = "bge-m3"
    host: str = "http://host.docker.internal:11434"
    request_timeout: float = 60

class OpenAILLMSettings(SettingBase):
    identifier: str = "openai_llm"
    display_name: str = "OpenAI LLM"
    description: str = "OpenAI LLM provider settings"
    model: str = "gpt-3.5-turbo"
    api_key: str = ""
    max_tokens: Optional[int] = None

class OpenAIEmbedSettings(SettingBase):
    identifier: str = "openai_embed"
    display_name: str = "OpenAI Embeddings"
    description: str = "OpenAI embedding provider settings"
    model: str = "text-embedding-3-large"
    api_key: str = ""

# Provider-specific settings
class AnthropicLLMSettings(SettingBase):
    identifier: str = "anthropic_llm"
    display_name: str = "Anthropic LLM"
    description: str = "Anthropic LLM provider settings"
    model: str = "claude-3-sonnet"
    api_key: str = ""

class GroqLLMSettings(SettingBase):
    identifier: str = "groq_llm"
    display_name: str = "Groq LLM"
    description: str = "Groq LLM provider settings"
    model: str = "mixtral-8x7b-v0.1"
    api_key: str = ""

class GeminiLLMSettings(SettingBase):
    identifier: str = "gemini_llm"
    display_name: str = "Gemini LLM"
    description: str = "Gemini LLM provider settings"
    model: str = "gemini-pro"
    api_key: str = ""

class GeminiEmbedSettings(SettingBase):
    identifier: str = "gemini_embed"
    display_name: str = "Gemini Embeddings"
    description: str = "Gemini Embeddings provider settings"
    model: str = "embedding-001"
    api_key: str = ""

class MistralLLMSettings(SettingBase):
    identifier: str = "mistral_llm"
    display_name: str = "Mistral LLM"
    description: str = "Mistral LLM provider settings"
    model: str = "mistral-medium"
    api_key: str = ""

class MistralEmbedSettings(SettingBase):
    identifier: str = "mistral_embed"
    display_name: str = "Mistral Embeddings"
    description: str = "Mistral Embeddings provider settings"
    model: str = "mistral-embed"
    api_key: str = ""

class AzureOpenAILLMSettings(SettingBase):
    identifier: str = "azure-openai_llm"
    display_name: str = "Azure OpenAI LLM"
    description: str = "Azure OpenAI LLM provider settings"
    model: str = "gpt-4"
    api_key: str = ""
    endpoint: str = ""
    api_version: str = ""
    deployment_name: str = ""

class AzureOpenAIEmbedSettings(SettingBase):
    identifier: str = "azure-openai_embed"
    display_name: str = "Azure OpenAI Embeddings"
    description: str = "Azure OpenAI Embeddings provider settings"
    model: str = "text-embedding-ada-002"
    api_key: str = ""
    endpoint: str = ""
    api_version: str = ""
    deployment_name: str = ""

class TGILLMSettings(SettingBase):
    identifier: str = "tgi_llm"
    display_name: str = "Text Generation Inference LLM"
    description: str = "Text Generation Inference LLM provider settings"
    model: str = "llama3.1"
    host: str = ""
    request_timeout: float = 500

class FastEmbedEmbedSettings(SettingBase):
    identifier: str = "fastembed_embed"
    display_name: str = "FastEmbed Embeddings"
    description: str = "FastEmbed embedding provider settings"
    embedding_model: str = "all-MiniLM-L6-v2"

class TEIEmbedSettings(SettingBase):
    identifier: str = "tei_embed"
    display_name: str = "Text Embeddings Inference Embeddings"
    description: str = "Text Embeddings Inference embedding provider settings"
    embedding_model: str = "nvidia/NV-Embed-v2"
    embedding_host: str = ""

class AppSettings(SettingBase):
    identifier: str = "app"
    display_name: str = "App"
    description: str = "General app settings"

    llm_model_provider: Literal[
        "ollama_llm", "openai_llm", 
        "text-generation-inference", "anthropic_llm", "groq_llm", 
        "gemini_llm", "mistral_llm", "azure-openai_llm"
    ] = "ollama_llm"
    
    # General settings
    top_k: int = 15
    max_iterations: int = 14
    temperature: float = 0.7
    
    system_prompt: str = (
        "You are an helpful personal assistant, be friendly with the user, talk to him like you are its helpful best friend. "
        "Act like you know him very well and like you know everything that you retrieve via the tools.\n"
        "You can use tools to answer user questions.\n"
        "You can access to the files of the user containing personal information about the user, you can use it to answer personal questions.\n"
        "When the user is talking at the first person, he is talking about himself. Use the tool to get personal information needed to answer.\n"
        "In your final answer strictly answer to the user question, do not go off topic or talk about tools used.\n"
    )