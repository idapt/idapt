export interface AppSettings {
  model_provider: string;
  custom_ollama_host: string;
  tgi_host: string;
  ollama_request_timeout: number;
  tgi_request_timeout: number;
  model: string;
  embedding_model_provider: string;
  embedding_model: string;
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
  //"text-generation-inference",
  /*"anthropic",
  "groq",
  "gemini",
  "mistral",
  "azure-openai",
  "t-systems",*/
] as const;

export const EMBEDDING_PROVIDER_OPTIONS = [
  "integrated_ollama",
  "custom_ollama",
  /*"fastembed",
  "openai",
  "azure-openai",
  "gemini",
  "mistral",*/
] as const;