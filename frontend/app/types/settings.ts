export interface SettingBase {
  identifier: string;
  display_name: string;
  description: string | null;
}

export interface AppSettings extends SettingBase {
  llm_model_provider: string;
  embedding_model_provider: string;
  embedding_dim: string;
  top_k: number;
  max_iterations: number;
  temperature: number;
  system_prompt: string;
}

// Provider-specific settings types
export interface OllamaSettings extends SettingBase {
  llm_model: string;
  llm_host: string;
  llm_request_timeout: number;
  embedding_model: string;
  embedding_host: string;
  embedding_request_timeout: number;
}

export interface OpenAISettings extends SettingBase {
  llm_model: string;
  api_key: string;
  embedding_model: string;
  max_tokens?: number;
}

export interface AnthropicSettings extends SettingBase {
  llm_model: string;
  api_key: string;
}

export interface GroqSettings extends SettingBase {
  llm_model: string;
  api_key: string;
}

export interface GeminiSettings extends SettingBase {
  llm_model: string;
  api_key: string;
  embedding_model: string;
}

export interface MistralSettings extends SettingBase {
  llm_model: string;
  api_key: string;
  embedding_model: string;
}

export interface AzureOpenAISettings extends SettingBase {
  llm_model: string;
  api_key: string;
  endpoint: string;
  api_version: string;
  deployment_name: string;
  embedding_model: string;
  embedding_deployment_name: string;
}

export interface TGISettings extends SettingBase {
  llm_model: string;
  llm_host: string;
  llm_request_timeout: number;
}

export interface FastEmbedSettings extends SettingBase {
  embedding_model: string;
}

export interface TEISettings extends SettingBase {
  embedding_model: string;
  embedding_host: string;
}

export const LLM_MODEL_PROVIDER_OPTIONS = [
  "ollama",
  "openai",
  //"text-generation-inference",
  //"anthropic",
  //"groq",
  //"gemini",
  //"mistral",
  //"azure-openai",
] as const;

export const LLM_MODEL_OPTIONS: Record<string, string[]> = {
  ollama: ["llama3.1:8b", "mistral:7b", "mixtral:8x7b", "phi:latest", "custom"],
  openai: ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo", "custom"],
  //anthropic: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1", "custom"],
  //groq: ["mixtral-8x7b-v0.1", "llama2-70b-v2-q4_0", "custom"],
  //gemini: ["gemini-pro", "gemini-pro-vision", "custom"],
  //mistral: ["mistral-tiny", "mistral-small", "mistral-medium", "custom"],
  //"azure-openai": ["gpt-4", "gpt-35-turbo", "custom"],
  //"text-generation-inference": ["llama3.1", "mistral", "mixtral", "custom"],
};

export const EMBEDDING_PROVIDER_OPTIONS = [
  "ollama",
  //"fastembed",
  "openai",
  //"azure-openai",
  //"gemini",
  //"mistral",
  //"text-embeddings-inference",
] as const;
export const EMBEDDING_MODEL_OPTIONS: Record<string, string[]> = {
  ollama: ["Losspost/stella_en_1.5b_v5", "bge-m3", "nomic-embed-text", "custom"],
  openai: ["text-embedding-3-large", "text-embedding-3-small", "custom"],
  //"azure-openai": ["text-embedding-ada-002", "custom"],
  //gemini: ["embedding-001", "custom"],
  //mistral: ["mistral-embed", "custom"],
  //fastembed: ["all-MiniLM-L6-v2", "paraphrase-multilingual-mpnet-base-v2", "custom"],
  //"text-embeddings-inference": ["nvidia/NV-Embed-v2", "BAAI/bge-base-en-v1.5", "custom"],
};
