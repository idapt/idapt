from typing import Dict
import os
from llama_index.core.settings import Settings
from llama_index.core.constants import DEFAULT_TEMPERATURE
from app.settings.app_settings import AppSettings
from app.settings.model_providers import *

def init_llm():
    """Initialize LLM based on model provider setting"""
    model_provider = AppSettings.model_provider
    match model_provider:
        case "openai":
            return init_openai_llm()
        case "groq":
            return init_groq_llm()
        case "integrated_ollama":
            return init_integrated_ollama_llm()
        case "custom_ollama":
            return init_custom_ollama_llm()
        case "text-generation-inference":
            return init_tgi_llm()
        case "anthropic":
            return init_anthropic_llm()
        case "gemini":
            return init_gemini_llm()
        case "mistral":
            return init_mistral_llm()
        case "azure-openai":
            return init_azure_openai_llm()
        case "t-systems":
            from .llmhub import init_llmhub_llm
            return init_llmhub_llm()
        case _:
            raise ValueError(f"Invalid model provider: {model_provider}")

def init_embedding_model():
    """Initialize embedding model based on embedding_model_provider setting"""
    provider = AppSettings.embedding_model_provider
    match provider:
        case "openai":
            return init_openai_embedding()
        case "integrated_ollama":
            return init_integrated_ollama_embedding()
        case "custom_ollama":
            return init_custom_ollama_embedding()
        case "azure-openai":
            return init_azure_openai_embedding()
        case "gemini":
            return init_gemini_embedding()
        case "mistral":
            return init_mistral_embedding()
        case "fastembed":
            return init_fastembed_embedding()
        case _:
            raise ValueError(f"Invalid embedding model provider: {provider}") 