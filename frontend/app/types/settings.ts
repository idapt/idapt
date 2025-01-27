export interface Setting {
  identifier: string;
  schema_identifier: string;
  setting_schema_json: string;
  value_json: string;
}

export interface FieldSchema {
  type: string;
  title?: string;
  description?: string;
  default?: any;
  minimum?: number;
  maximum?: number;
  enum?: string[];
  format?: string;
}

export interface JsonSchema {
  properties: Record<string, FieldSchema>;
  required: string[];
  title: string;
  description?: string;
}

export interface SettingsEditorProps {
  setting: Setting;
  onSave: (setting: Setting) => Promise<void>;
  onDelete: () => Promise<void>;
  onCancel: () => void;
}

// Schema identifier list
export const SCHEMA_IDENTIFIER_OPTIONS = [
  // App Settings
  "app",
  // LLM Settings
  "ollama_llm",
  "openai_llm",
  //"text-generation-inference",
  //"anthropic",
  //"groq",
  //"gemini",
  //"mistral",
  //"azure-openai",
  // Embedding Settings
  "ollama_embed",
  //"fastembed",
  "openai_embed",
  //"azure-openai",
  //"gemini",
  //"mistral",
  //"text-embeddings-inference",
] as const;