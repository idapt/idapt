export interface AppSettings {
  model_provider: string;
  model: string;
  embedding_model: string;
  embedding_dim: string;
  top_k: number;
  system_prompt: string;
}

export const MODEL_PROVIDER_OPTIONS = [
  "ollama",
  /*"openai",
  "anthropic",
  "groq",
  "gemini",
  "mistral",
  "azure-openai",
  "t-systems",*/
] as const;