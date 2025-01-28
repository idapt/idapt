from pydantic import BaseModel
from typing import Literal, Optional, Dict, Type, List

class CreateSettingRequest(BaseModel):
    schema_identifier: str

class UpdateSettingRequest(BaseModel):
    values_to_update_json: str

class SettingResponse(BaseModel):
    identifier: str
    schema_identifier: str
    setting_schema_json: str
    value_json: str

class AllSettingsResponse(BaseModel):
    data: List[SettingResponse]

class SettingBase(BaseModel):

    def update_value(self, new_values: dict):
        """
        New values are a dictionary of key-value pairs to update in the current setting value
        """
        # Validate the new new_values format
        if not isinstance(new_values, dict):
            raise ValueError("New values must be a dictionary of key-value pairs to update in the current setting value")
        # For each key in the new value, update the corresponding field in the current setting value
        for key, value in new_values.items():
            # Check if the key exists in the current setting value
            if hasattr(self, key):
                # Update the field in the current setting value
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid key: {key}")


# LLM Settings
class OllamaLLMSettings(SettingBase):
    model: str = "deepseek-r1:8b" #Literal["llama3.1:8b", "mistral:7b", "mixtral:8x7b", "phi:latest", "custom"] = "llama3.1:8b"
    host: str = "http://host.docker.internal:11434"
    request_timeout: float = 300

class OpenAILLMSettings(SettingBase):
    model: Literal["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo", "custom"] = "gpt-3.5-turbo"
    api_key: str = ""
    max_tokens: Optional[int] = None

# Provider-specific settings
class AnthropicLLMSettings(SettingBase):
    display_name: str = "Anthropic LLM"
    description: str = "Anthropic LLM provider settings"
    model: Literal["claude-3-sonnet", "claude-3-haiku", "claude-2.1", "custom"] = "claude-3-sonnet"
    api_key: str = ""

class GroqLLMSettings(SettingBase):
    model: Literal["mixtral-8x7b-v0.1", "llama2-70b-v2-q4_0", "custom"] = "mixtral-8x7b-v0.1"
    api_key: str = ""

class GeminiLLMSettings(SettingBase):
    model: Literal["gemini-pro", "gemini-pro-vision", "custom"] = "gemini-pro"
    api_key: str = ""


class MistralLLMSettings(SettingBase):
    model: Literal["mistral-tiny", "mistral-small", "mistral-medium", "custom"] = "mistral-medium"
    api_key: str = ""

class AzureOpenAILLMSettings(SettingBase):
    model: Literal["gpt-4", "gpt-35-turbo", "custom"] = "gpt-4"
    api_key: str = ""
    endpoint: str = ""
    api_version: str = ""
    deployment_name: str = ""

class TGILLMSettings(SettingBase):
    model: Literal["llama3.1", "mistral", "mixtral", "custom"] = "llama3.1"
    host: str = ""
    request_timeout: float = 500


# Embeddings settings
class OllamaEmbedSettings(SettingBase):
    model: str = "bge-m3" #Literal["Losspost/stella_en_1.5b_v5", "bge-m3", "nomic-embed-text", "custom"] = "bge-m3"
    host: str = "http://host.docker.internal:11434"
    request_timeout: float = 300

class OpenAIEmbedSettings(SettingBase):
    model: Literal["text-embedding-3-large", "text-embedding-3-small", "custom"] = "text-embedding-3-small"
    api_key: str = ""

class GeminiEmbedSettings(SettingBase):
    model: Literal["embedding-001", "custom"] = "embedding-001"
    api_key: str = ""


class FastEmbedEmbedSettings(SettingBase):
    embedding_model: Literal["all-MiniLM-L6-v2", "paraphrase-multilingual-mpnet-base-v2", "custom"] = "all-MiniLM-L6-v2"

class MistralEmbedSettings(SettingBase):
    model: Literal["mistral-embed", "custom"] = "mistral-embed"
    api_key: str = ""

class AzureOpenAIEmbedSettings(SettingBase):
    model: Literal["text-embedding-ada-002", "custom"] = "text-embedding-ada-002"
    api_key: str = ""
    endpoint: str = ""
    api_version: str = ""
    deployment_name: str = ""


class TEIEmbedSettings(SettingBase):
    embedding_model: Literal["nvidia/NV-Embed-v2", "BAAI/bge-base-en-v1.5", "custom"] = "nvidia/NV-Embed-v2"
    embedding_host: str = ""

class AppSettings(SettingBase):
    llm_setting_identifier: str = "default_ollama_llm" # Default to ollama_llm for first init
    
    # General settings
    top_k: int = 15
    max_iterations: int = 14
    temperature: float = 0.7
    
    system_prompt: str = (
        "You are an helpful personal assistant, be friendly with the user, talk to him like you are its helpful best friend.\n"
        "Act like you know him very well and like you know everything that you retrieve via the tools.\n"
        "You can use the tools to access files that contain personal information about the user. Each tool correspond to a datasource.\n"
        "When you don't know about something the user is talking about, he is probably talking about something personal. In this case, use the tools to get the missing personal context you need to answer.\n"
        "In your final answer strictly answer to the user question, do not go off topic or talk about tools used."
    )

# Used to get the model class for a setting via the schema_identifier
SETTING_CLASSES: Dict[str, Type[SettingBase]] = {
    # App Settings
    "app": AppSettings,
    # LLM Settings
    "ollama_llm": OllamaLLMSettings,
    "openai_llm": OpenAILLMSettings,
    "anthropic_llm": AnthropicLLMSettings,
    "groq_llm": GroqLLMSettings,
    "gemini_llm": GeminiLLMSettings,
    "mistral_llm": MistralLLMSettings,
    "azure-openai_llm": AzureOpenAILLMSettings,
    "tgi_llm": TGILLMSettings,
    # Embedding Settings
    "ollama_embed": OllamaEmbedSettings,
    "openai_embed": OpenAIEmbedSettings,
    "azure_openai_embed": AzureOpenAIEmbedSettings,
    "mistral_embed": MistralEmbedSettings,
    "gemini_embed": GeminiEmbedSettings,
    "tei_embed": TEIEmbedSettings,
    "fastembed_embed": FastEmbedEmbedSettings,
}
