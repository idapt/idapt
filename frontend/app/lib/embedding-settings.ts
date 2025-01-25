import {
  OllamaEmbedSettings,
  OpenAIEmbedSettings,
  FastEmbedEmbedSettings,
  TEIEmbedSettings
} from "@/app/types/settings";

export type EmbeddingSettings = 
  | OllamaEmbedSettings 
  | OpenAIEmbedSettings 
  | FastEmbedEmbedSettings 
  | TEIEmbedSettings;

export function parseEmbeddingSettings(provider: string, settingsJson: string): EmbeddingSettings {
  try {
    const settings = JSON.parse(settingsJson);
    
    switch (provider) {
      case "ollama_embed":
        return {
          identifier: "ollama_embed",
          display_name: "Ollama Embeddings",
          description: "Ollama embedding provider settings",
          model: settings.model || "Losspost/stella_en_1.5b_v5",
          host: settings.host || "http://host.docker.internal:11434",
          request_timeout: settings.request_timeout || 60
        };
      
      case "openai_embed":
        return {
          identifier: "openai_embed",
          display_name: "OpenAI Embeddings",
          description: "OpenAI embedding provider settings",
          model: settings.model || "text-embedding-3-small",
          api_key: settings.api_key || ""
        };
      
      default:
        throw new Error(`Unsupported embedding provider: ${provider}`);
    }
  } catch (error) {
    // Return default settings if parsing fails
    return getDefaultEmbeddingSettings(provider);
  }
}

function getDefaultEmbeddingSettings(provider: string): EmbeddingSettings {
  switch (provider) {
    case "ollama_embed":
      return {
        identifier: "ollama_embed",
        display_name: "Ollama Embeddings",
        description: "Ollama embedding provider settings",
        model: "Losspost/stella_en_1.5b_v5",
        host: "http://host.docker.internal:11434",
        request_timeout: 60
      };
    
    case "openai_embed":
      return {
        identifier: "openai_embed",
        display_name: "OpenAI Embeddings",
        description: "OpenAI embedding provider settings",
        model: "text-embedding-3-small",
        api_key: ""
      };
    
    default:
      throw new Error(`Unsupported embedding provider: ${provider}`);
  }
} 