"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Button } from "../button";
import { Input } from "../input";
import { Textarea } from "../textarea";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../select";
import { AppSettings, LLM_MODEL_PROVIDER_OPTIONS, EMBEDDING_PROVIDER_OPTIONS, LLM_MODEL_OPTIONS, EMBEDDING_MODEL_OPTIONS } from "@/app/types/settings";
import { getSettings, updateSettings } from "@/app/api/settings";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const isCustomEmbeddingModel = (provider: string, modelName: string): boolean => {
  const predefinedModels = EMBEDDING_MODEL_OPTIONS[provider] || [];
  return !predefinedModels.includes(modelName) || modelName === "custom";
};

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const isCustomModel = (provider: string, modelName: string): boolean => {
    const predefinedModels = LLM_MODEL_OPTIONS[provider] || [];
    return !predefinedModels.includes(modelName) || modelName === "custom";
  };

  useEffect(() => {
    if (isOpen) {
      getSettings()
        .then(setSettings)
        .catch(error => setSaveError(error.message));
    }
  }, [isOpen]);

  const handleSave = async () => {
    if (!settings) return;
    
    try {
      setSaveError(null);
      setIsSaving(true);
      await updateSettings(settings);
      onClose();
    } catch (error) {
      if (error instanceof Error) {
        try {
          const errorData = JSON.parse(error.message);
          if (errorData.errors) {
            // Handle validation errors
            setSaveError(errorData.errors.join('\n'));
          } else {
            setSaveError(errorData.message || 'An unexpected error occurred');
          }
        } catch {
          setSaveError(error.message);
        }
      } else {
        setSaveError('An unexpected error occurred');
      }
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen || !settings) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-2xl p-6 overflow-y-auto max-h-[90vh]">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Settings</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </Button>
        </div>

        <div className="space-y-4">
          {saveError && (
            <div className="text-red-500 text-sm mb-4">{saveError}</div>
          )}
          {Object.entries(errors).map(([field, error]) => (
            <div key={field} className="text-red-500 text-sm">
              {field}: {error}
            </div>
          ))}

          <div className="space-y-2">
            <label className="text-sm font-medium">Model Provider</label>
            <Select
              value={settings.llm_model_provider}
              onValueChange={(value) => setSettings({...settings, llm_model_provider: value})}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a model provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {LLM_MODEL_PROVIDER_OPTIONS.map((provider) => (
                    <SelectItem key={provider} value={provider}>
                      {provider}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          {/* Only show the custom ollama host input if the model provider is custom_ollama */}
          {settings.llm_model_provider === "custom_ollama" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Custom Ollama Host</label>
              <Input
                value={settings.custom_ollama.llm_host}
                onChange={(e) => setSettings({...settings, custom_ollama: {...settings.custom_ollama, llm_host: e.target.value}})}
              />
            </div>
          )}

          {/* Only show the OpenAI API key input if the model provider is openai */}
          {settings.llm_model_provider === "openai" && (  
            <div className="space-y-2">
              <label className="text-sm font-medium">OpenAI API Key</label>
              <Input
                type="password"
                value={settings.openai.api_key}
                onChange={(e) => setSettings({...settings, openai: {...settings.openai, api_key: e.target.value}})}
              />
            </div>
          )}

          {/* Only show the Text Generation Inference host input if the model provider is text-generation-inference */}
          {settings.llm_model_provider === "text-generation-inference" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Text Generation Inference Host</label>
              <Input
                value={settings.tgi.llm_host}
                onChange={(e) => setSettings({...settings, tgi: {...settings.tgi, llm_host: e.target.value}})}
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Model</label>
            <Select
              value={
                settings.llm_model_provider === "integrated_ollama" ? (isCustomModel(settings.llm_model_provider, settings.integrated_ollama.llm_model) ? "custom" : settings.integrated_ollama.llm_model) :
                settings.llm_model_provider === "custom_ollama" ? (isCustomModel(settings.llm_model_provider, settings.custom_ollama.llm_model) ? "custom" : settings.custom_ollama.llm_model) :
                settings.llm_model_provider === "openai" ? (isCustomModel(settings.llm_model_provider, settings.openai.llm_model) ? "custom" : settings.openai.llm_model) :
                settings.llm_model_provider === "anthropic" ? (isCustomModel(settings.llm_model_provider, settings.anthropic.llm_model) ? "custom" : settings.anthropic.llm_model) :
                settings.llm_model_provider === "groq" ? (isCustomModel(settings.llm_model_provider, settings.groq.llm_model) ? "custom" : settings.groq.llm_model) :
                settings.llm_model_provider === "gemini" ? (isCustomModel(settings.llm_model_provider, settings.gemini.llm_model) ? "custom" : settings.gemini.llm_model) :
                settings.llm_model_provider === "mistral" ? (isCustomModel(settings.llm_model_provider, settings.mistral.llm_model) ? "custom" : settings.mistral.llm_model) :
                settings.llm_model_provider === "azure-openai" ? (isCustomModel(settings.llm_model_provider, settings.azure_openai.llm_model) ? "custom" : settings.azure_openai.llm_model) :
                settings.llm_model_provider === "text-generation-inference" ? (isCustomModel(settings.llm_model_provider, settings.tgi.llm_model) ? "custom" : settings.tgi.llm_model) :
                ""
              }
              onValueChange={(value) => {
                if (!settings) return;

                const providerSettings = {
                  integrated_ollama: settings.integrated_ollama,
                  custom_ollama: settings.custom_ollama,
                  openai: settings.openai,
                  anthropic: settings.anthropic,
                  groq: settings.groq,
                  gemini: settings.gemini,
                  mistral: settings.mistral,
                  azure_openai: settings.azure_openai,
                  tgi: settings.tgi,
                };

                // If selecting "custom", don't change the actual model value yet
                if (value === "custom") {
                  setSettings({
                    ...settings,
                    [settings.llm_model_provider]: {
                      ...providerSettings[settings.llm_model_provider as keyof typeof providerSettings],
                      llm_model: value
                    }
                  });
                } else {
                  setSettings({
                    ...settings,
                    [settings.llm_model_provider]: {
                      ...providerSettings[settings.llm_model_provider as keyof typeof providerSettings],
                      llm_model: value
                    }
                  });
                }
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {LLM_MODEL_OPTIONS[settings.llm_model_provider]?.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>

            {isCustomModel(settings.llm_model_provider, 
              settings.llm_model_provider === "integrated_ollama" ? settings.integrated_ollama.llm_model :
              settings.llm_model_provider === "custom_ollama" ? settings.custom_ollama.llm_model :
              settings.llm_model_provider === "openai" ? settings.openai.llm_model :
              settings.llm_model_provider === "anthropic" ? settings.anthropic.llm_model :
              settings.llm_model_provider === "groq" ? settings.groq.llm_model :
              settings.llm_model_provider === "gemini" ? settings.gemini.llm_model :
              settings.llm_model_provider === "mistral" ? settings.mistral.llm_model :
              settings.llm_model_provider === "azure-openai" ? settings.azure_openai.llm_model :
              settings.llm_model_provider === "text-generation-inference" ? settings.tgi.llm_model :
              ""
            ) && (
              <div className="mt-2">
                <Input
                  placeholder="Enter custom model name"
                  value={
                    settings.llm_model_provider === "integrated_ollama" ? settings.integrated_ollama.llm_model :
                    settings.llm_model_provider === "custom_ollama" ? settings.custom_ollama.llm_model :
                    settings.llm_model_provider === "openai" ? settings.openai.llm_model :
                    settings.llm_model_provider === "anthropic" ? settings.anthropic.llm_model :
                    settings.llm_model_provider === "groq" ? settings.groq.llm_model :
                    settings.llm_model_provider === "gemini" ? settings.gemini.llm_model :
                    settings.llm_model_provider === "mistral" ? settings.mistral.llm_model :
                    settings.llm_model_provider === "azure-openai" ? settings.azure_openai.llm_model :
                    settings.llm_model_provider === "text-generation-inference" ? settings.tgi.llm_model :
                    ""
                  }
                  onChange={(e) => {
                    if (!settings) return;
                  
                    const providerSettings = {
                      integrated_ollama: settings.integrated_ollama,
                      custom_ollama: settings.custom_ollama,
                      openai: settings.openai,
                      anthropic: settings.anthropic,
                      groq: settings.groq,
                      gemini: settings.gemini,
                      mistral: settings.mistral,
                      azure_openai: settings.azure_openai,
                      tgi: settings.tgi,
                    };
                  
                    setSettings({
                      ...settings,
                      [settings.llm_model_provider]: {
                        ...providerSettings[settings.llm_model_provider as keyof typeof providerSettings],
                        llm_model: e.target.value
                      }
                    });
                  }}
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Model Provider</label>
            <Select
              value={settings.embedding_model_provider}
              onValueChange={(value) => setSettings({...settings, embedding_model_provider: value})}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select an embedding provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {EMBEDDING_PROVIDER_OPTIONS.map((provider) => (
                    <SelectItem key={provider} value={provider}>
                      {provider}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Model</label>
            <Select
              value={
                settings.embedding_model_provider === "integrated_ollama" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.integrated_ollama.embedding_model) ? "custom" : settings.integrated_ollama.embedding_model) :
                settings.embedding_model_provider === "custom_ollama" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.custom_ollama.embedding_model) ? "custom" : settings.custom_ollama.embedding_model) :
                settings.embedding_model_provider === "openai" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.openai.embedding_model) ? "custom" : settings.openai.embedding_model) :
                settings.embedding_model_provider === "azure-openai" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.azure_openai.embedding_model) ? "custom" : settings.azure_openai.embedding_model) :
                settings.embedding_model_provider === "gemini" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.gemini.embedding_model) ? "custom" : settings.gemini.embedding_model) :
                settings.embedding_model_provider === "mistral" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.mistral.embedding_model) ? "custom" : settings.mistral.embedding_model) :
                settings.embedding_model_provider === "fastembed" ? (isCustomEmbeddingModel(settings.embedding_model_provider, settings.fastembed.embedding_model) ? "custom" : settings.fastembed.embedding_model) :
                ""
              }
              onValueChange={(value) => {
                const modelKey = 
                  settings.embedding_model_provider === "integrated_ollama" ? "integrated_ollama.embedding_model" :
                  settings.embedding_model_provider === "custom_ollama" ? "custom_ollama.embedding_model" :
                  settings.embedding_model_provider === "openai" ? "openai.embedding_model" :
                  settings.embedding_model_provider === "azure-openai" ? "azure_openai.embedding_model" :
                  settings.embedding_model_provider === "gemini" ? "gemini.embedding_model" :
                  settings.embedding_model_provider === "mistral" ? "mistral.embedding_model" :
                  settings.embedding_model_provider === "fastembed" ? "fastembed.embedding_model" :
                  null;
                
                if (modelKey) {
                  if (value === "custom") {
                    setSettings({
                      ...settings,
                      [modelKey]: value
                    });
                  } else {
                    setSettings({
                      ...settings,
                      [modelKey]: value
                    });
                  }
                }
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {EMBEDDING_MODEL_OPTIONS[settings.embedding_model_provider]?.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>

            {isCustomEmbeddingModel(settings.embedding_model_provider,
              settings.embedding_model_provider === "integrated_ollama" ? settings.integrated_ollama.embedding_model :
              settings.embedding_model_provider === "custom_ollama" ? settings.custom_ollama.embedding_model :
              settings.embedding_model_provider === "openai" ? settings.openai.embedding_model :
              settings.embedding_model_provider === "azure-openai" ? settings.azure_openai.embedding_model :
              settings.embedding_model_provider === "gemini" ? settings.gemini.embedding_model :
              settings.embedding_model_provider === "mistral" ? settings.mistral.embedding_model :
              settings.embedding_model_provider === "fastembed" ? settings.fastembed.embedding_model :
              ""
            ) && (
              <div className="mt-2">
                <Input
                  placeholder="Enter custom embedding model name"
                  value={
                    settings.embedding_model_provider === "integrated_ollama" ? (settings.integrated_ollama.embedding_model === "custom" ? "" : settings.integrated_ollama.embedding_model) :
                    settings.embedding_model_provider === "custom_ollama" ? (settings.custom_ollama.embedding_model === "custom" ? "" : settings.custom_ollama.embedding_model) :
                    settings.embedding_model_provider === "openai" ? (settings.openai.embedding_model === "custom" ? "" : settings.openai.embedding_model) :
                    settings.embedding_model_provider === "azure-openai" ? (settings.azure_openai.embedding_model === "custom" ? "" : settings.azure_openai.embedding_model) :
                    settings.embedding_model_provider === "gemini" ? (settings.gemini.embedding_model === "custom" ? "" : settings.gemini.embedding_model) :
                    settings.embedding_model_provider === "mistral" ? (settings.mistral.embedding_model === "custom" ? "" : settings.mistral.embedding_model) :
                    settings.embedding_model_provider === "fastembed" ? (settings.fastembed.embedding_model === "custom" ? "" : settings.fastembed.embedding_model) :
                    ""
                  }
                  onChange={(e) => {
                    const modelKey = 
                      settings.embedding_model_provider === "integrated_ollama" ? "ollama_embedding_model" :
                      settings.embedding_model_provider === "custom_ollama" ? "ollama_embedding_model" :
                      settings.embedding_model_provider === "openai" ? "openai_embedding_model" :
                      settings.embedding_model_provider === "azure-openai" ? "azure_openai_embedding_model" :
                      settings.embedding_model_provider === "gemini" ? "gemini_embedding_model" :
                      settings.embedding_model_provider === "mistral" ? "mistral_embedding_model" :
                      settings.embedding_model_provider === "fastembed" ? "fastembed_embedding_model" :
                      null;
                    
                    if (modelKey) {
                      setSettings({
                        ...settings,
                        [modelKey]: e.target.value
                      });
                    }
                  }}
                />
              </div>
            )}
          </div>

          {settings.embedding_model_provider === "custom_ollama" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Custom Ollama Embedding Host</label>
              <Input
                value={settings.custom_ollama.embedding_host}
                onChange={(e) => setSettings({...settings, custom_ollama: {...settings.custom_ollama, embedding_host: e.target.value}})}
                placeholder="http://localhost:11434"
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Dimensions</label>
            <Input
              value={settings.embedding_dim}
              onChange={(e) => setSettings({...settings, embedding_dim: e.target.value})}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Top K Results</label>
            <Input
              type="number"
              value={settings.top_k}
              onChange={(e) => setSettings({...settings, top_k: parseInt(e.target.value)})}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Max Agent Iterations</label>
            <Input
              type="number"
              value={settings.max_iterations}
              onChange={(e) => setSettings({...settings, max_iterations: parseInt(e.target.value)})}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Files Tool Description</label>
            <Textarea
              value={settings.files_tool_description}
              onChange={(e) => setSettings({...settings, files_tool_description: e.target.value})}
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">System Prompt</label>
            <Textarea
              value={settings.system_prompt}
              onChange={(e) => setSettings({...settings, system_prompt: e.target.value})}
              rows={4}
            />
          </div>

          {/* Only show the ollama request timeout input if the model provider is integrated_ollama or custom_ollama */}
          {(settings.llm_model_provider === "integrated_ollama" || settings.llm_model_provider === "custom_ollama") && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Ollama Request Timeout (s)</label>
              <Input
                type="number"
                value={settings.integrated_ollama.llm_request_timeout}
                onChange={(e) => setSettings({...settings, integrated_ollama: {...settings.integrated_ollama, llm_request_timeout: parseInt(e.target.value)}})}
              />
            </div>
          )}

          {/* Only show the Text Generation Inference request timeout input if the model provider is text-generation-inference */}
          {settings.llm_model_provider === "text-generation-inference" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Text Generation Inference Request Timeout (s)</label>
              <Input
                type="number"
                value={settings.tgi.llm_request_timeout}
                onChange={(e) => setSettings({...settings, tgi: {...settings.tgi, llm_request_timeout: parseInt(e.target.value)}})}
              />
            </div>
          )}

          {settings.embedding_model_provider === "text-embeddings-inference" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Text Embeddings Inference Host</label>
              <Input
                value={settings.tei.embedding_host}
                onChange={(e) => setSettings({...settings, tei: {...settings.tei, embedding_host: e.target.value}})}
                placeholder="http://localhost:8080"
              />
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 