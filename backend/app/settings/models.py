from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, Optional

# Provider-specific settings
class OllamaSettings(BaseModel):
    llm_model: str = "llama3.1:8b"
    llm_host: str = "http://host.docker.internal:11434"
    llm_request_timeout: float = 300
    embedding_model: str = "Losspost/stella_en_1.5b_v5"
    embedding_host: str = "http://host.docker.internal:11434"
    embedding_request_timeout: float = 60

class OpenAISettings(BaseModel):
    llm_model: str = "gpt-3.5-turbo"
    api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    max_tokens: Optional[int] = None

class AnthropicSettings(BaseModel):
    llm_model: str = "claude-3-sonnet"
    api_key: str = ""

class GroqSettings(BaseModel):
    llm_model: str = "mixtral-8x7b-v0.1"
    api_key: str = ""

class GeminiSettings(BaseModel):
    llm_model: str = "gemini-pro"
    api_key: str = ""
    embedding_model: str = "embedding-001"

class MistralSettings(BaseModel):
    llm_model: str = "mistral-medium"
    api_key: str = ""
    embedding_model: str = "mistral-embed"

class AzureOpenAISettings(BaseModel):
    llm_model: str = "gpt-4"
    api_key: str = ""
    endpoint: str = ""
    api_version: str = ""
    deployment_name: str = ""
    embedding_model: str = "text-embedding-ada-002"
    embedding_deployment_name: str = ""

class TGISettings(BaseModel):
    llm_model: str = "llama3.1"
    llm_host: str = ""
    llm_request_timeout: float = 500

class FastEmbedSettings(BaseModel):
    embedding_model: str = "all-MiniLM-L6-v2"

class TEISettings(BaseModel):
    embedding_model: str = "nvidia/NV-Embed-v2"
    embedding_host: str = ""

class AppSettings(BaseModel):
    llm_model_provider: Literal[
        "remote_ollama", "openai", 
        "text-generation-inference", "anthropic", "groq", 
        "gemini", "mistral", "azure-openai"
    ] = "remote_ollama"
    
    embedding_model_provider: Literal[
        "remote_ollama", "openai",
        "azure-openai", "gemini", "mistral", "fastembed",
        "text-embeddings-inference"
    ] = "remote_ollama"

    # Provider settings
    remote_ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    groq: GroqSettings = Field(default_factory=GroqSettings)
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)
    mistral: MistralSettings = Field(default_factory=MistralSettings)
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    tgi: TGISettings = Field(default_factory=TGISettings)
    fastembed: FastEmbedSettings = Field(default_factory=FastEmbedSettings)
    tei: TEISettings = Field(default_factory=TEISettings)

    # General settings
    embedding_dim: str = "1536"
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

    class Config:
        json_schema_extra = {
            #"example": {
                #"llm_model_provider": "remote_ollama",
                #"ollama_model": "llama3.1:8b",
                # ... other example values
            #}
        }
 