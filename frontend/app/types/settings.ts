export interface AppSettings {
  model_provider: string;
  custom_ollama_host: string;
  ollama_request_timeout: number;
  model: string;
  embedding_model: string;
  embedding_dim: string;
  top_k: number;
  system_prompt: string;
  max_iterations: number;
}

export const MODEL_PROVIDER_OPTIONS = [
  "integrated_ollama",
  "custom_ollama",
  /*"openai",
  "anthropic",
  "groq",
  "gemini",
  "mistral",
  "azure-openai",
  "t-systems",*/
] as const;