export interface AppSettings {
  model_provider: string;
  ollama_model: string;
  openai_model: string;
  anthropic_model: string;
  groq_model: string;
  gemini_model: string;
  mistral_model: string;
  azure_openai_model: string;
  tgi_model: string;
  custom_ollama_host: string;
  tgi_host: string;
  ollama_request_timeout: number;
  tgi_request_timeout: number;
  embedding_model_provider: string;
  ollama_embedding_model: string;
  openai_embedding_model: string;
  azure_openai_embedding_model: string;
  gemini_embedding_model: string;
  mistral_embedding_model: string;
  fastembed_embedding_model: string;
  embedding_dim: string;
  top_k: number;
  openai_api_key: string;
  system_prompt: string;
  max_iterations: number;
  files_tool_description: string;
}

export const MODEL_PROVIDER_OPTIONS = [
  "integrated_ollama",
  "custom_ollama",
  "openai",
  "text-generation-inference",
  "anthropic",
  "groq",
  "gemini",
  "mistral",
  "azure-openai",
] as const;

export const MODEL_OPTIONS: Record<string, string[]> = {
  integrated_ollama: ["llama3.1:8b", "mistral:7b", "mixtral:8x7b", "phi:latest", "custom"],
  custom_ollama: ["llama3.1:8b", "mistral:7b", "mixtral:8x7b", "phi:latest", "custom"],
  openai: ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo", "custom"],
  anthropic: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1", "custom"],
  groq: ["mixtral-8x7b-v0.1", "llama2-70b-v2-q4_0", "custom"],
  gemini: ["gemini-pro", "gemini-pro-vision", "custom"],
  mistral: ["mistral-tiny", "mistral-small", "mistral-medium", "custom"],
  "azure-openai": ["gpt-4", "gpt-35-turbo", "custom"],
  "text-generation-inference": ["llama3.1", "mistral", "mixtral", "custom"],
};

export const EMBEDDING_PROVIDER_OPTIONS = [
  "integrated_ollama",
  "custom_ollama",
  "fastembed",
  "openai",
  "azure-openai",
  "gemini",
  "mistral",
] as const;

export const EMBEDDING_MODEL_OPTIONS: Record<string, string[]> = {
  integrated_ollama: ["Losspost/stella_en_1.5b_v5", "bge-m3", "nomic-embed-text", "custom"],
  custom_ollama: ["Losspost/stella_en_1.5b_v5", "bge-m3", "nomic-embed-text", "custom"],
  openai: ["text-embedding-3-large", "text-embedding-3-small", "custom"],
  "azure-openai": ["text-embedding-ada-002", "custom"],
  gemini: ["embedding-001", "custom"],
  mistral: ["mistral-embed", "custom"],
  fastembed: ["all-MiniLM-L6-v2", "paraphrase-multilingual-mpnet-base-v2", "custom"],
};