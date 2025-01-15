from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, Optional

class SettingBase(BaseModel):
    identifier: str
    display_name: str
    description: Optional[str] = None

# Provider-specific settings
class OllamaSettings(SettingBase):
    identifier: str = "ollama"
    display_name: str = "Ollama"
    description: str = "Ollama LLM and embedding provider settings"
    llm_model: str = "llama3.1:8b"
    llm_host: str = "http://host.docker.internal:11434"
    llm_request_timeout: float = 300
    embedding_model: str = "Losspost/stella_en_1.5b_v5"
    embedding_host: str = "http://host.docker.internal:11434"
    embedding_request_timeout: float = 60

class OpenAISettings(SettingBase):
    identifier: str = "openai"
    display_name: str = "OpenAI"
    description: str = "OpenAI LLM and embedding provider settings"
    llm_model: str = "gpt-3.5-turbo"
    api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    max_tokens: Optional[int] = None

class AnthropicSettings(SettingBase):
    identifier: str = "anthropic"
    display_name: str = "Anthropic"
    description: str = "Anthropic LLM provider settings"
    llm_model: str = "claude-3-sonnet"
    api_key: str = ""

class GroqSettings(SettingBase):
    identifier: str = "groq"
    display_name: str = "Groq"
    description: str = "Groq LLM provider settings"
    llm_model: str = "mixtral-8x7b-v0.1"
    api_key: str = ""

class GeminiSettings(SettingBase):
    identifier: str = "gemini"
    display_name: str = "Gemini"
    description: str = "Gemini LLM provider settings"
    llm_model: str = "gemini-pro"
    api_key: str = ""
    embedding_model: str = "embedding-001"

class MistralSettings(SettingBase):
    identifier: str = "mistral"
    display_name: str = "Mistral"
    description: str = "Mistral LLM provider settings"
    llm_model: str = "mistral-medium"
    api_key: str = ""
    embedding_model: str = "mistral-embed"

class AzureOpenAISettings(SettingBase):
    identifier: str = "azure-openai"
    display_name: str = "Azure OpenAI"
    description: str = "Azure OpenAI LLM and embedding provider settings"
    llm_model: str = "gpt-4"
    api_key: str = ""
    endpoint: str = ""
    api_version: str = ""
    deployment_name: str = ""
    embedding_model: str = "text-embedding-ada-002"
    embedding_deployment_name: str = ""

class TGISettings(SettingBase):
    identifier: str = "tgi"
    display_name: str = "Text Generation Inference"
    description: str = "Text Generation Inference LLM provider settings"
    llm_model: str = "llama3.1"
    llm_host: str = ""
    llm_request_timeout: float = 500

class FastEmbedSettings(SettingBase):
    identifier: str = "fastembed"
    display_name: str = "FastEmbed"
    description: str = "FastEmbed embedding provider settings"
    embedding_model: str = "all-MiniLM-L6-v2"

class TEISettings(SettingBase):
    identifier: str = "tei"
    display_name: str = "Text Embeddings Inference"
    description: str = "Text Embeddings Inference embedding provider settings"
    embedding_model: str = "nvidia/NV-Embed-v2"
    embedding_host: str = ""

class AppSettings(SettingBase):
    identifier: str = "app"
    display_name: str = "App"
    description: str = "General app settings"

    llm_model_provider: Literal[
        "ollama", "openai", 
        "text-generation-inference", "anthropic", "groq", 
        "gemini", "mistral", "azure-openai"
    ] = "ollama"
    
    embedding_model_provider: Literal[
        "ollama", "openai",
        "azure-openai", "gemini", "mistral", "fastembed",
        "text-embeddings-inference"
    ] = "ollama"

    # General settings
    embedding_dim: int = 1536
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