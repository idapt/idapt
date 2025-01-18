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
import { 
  AppSettings, 
  OllamaSettings,
  OpenAISettings,
  AnthropicSettings,
  GroqSettings,
  GeminiSettings,
  MistralSettings,
  AzureOpenAISettings,
  TGISettings,
  FastEmbedSettings,
  TEISettings,
  LLM_MODEL_PROVIDER_OPTIONS, 
  EMBEDDING_PROVIDER_OPTIONS, 
  LLM_MODEL_OPTIONS, 
  EMBEDDING_MODEL_OPTIONS 
} from "@/app/types/settings";
import { useSettings } from "./settings-provider";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

// Helper function to check if a model is custom
const isCustomModel = (provider: string, modelName: string): boolean => {
  const predefinedModels = LLM_MODEL_OPTIONS[provider] || [];
  return !predefinedModels.includes(modelName) || modelName === "custom";
};

const isCustomEmbeddingModel = (provider: string, modelName: string): boolean => {
  const predefinedModels = EMBEDDING_MODEL_OPTIONS[provider] || [];
  return !predefinedModels.includes(modelName) || modelName === "custom";
};

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  // Main app settings state
  const [appSettings, setAppSettings] = useState<AppSettings | null>(null);
  
  // Provider-specific settings states
  const [ollamaSettings, setOllamaSettings] = useState<OllamaSettings | null>(null);
  const [openAISettings, setOpenAISettings] = useState<OpenAISettings | null>(null);
  const [anthropicSettings, setAnthropicSettings] = useState<AnthropicSettings | null>(null);
  const [groqSettings, setGroqSettings] = useState<GroqSettings | null>(null);
  const [geminiSettings, setGeminiSettings] = useState<GeminiSettings | null>(null);
  const [mistralSettings, setMistralSettings] = useState<MistralSettings | null>(null);
  const [azureOpenAISettings, setAzureOpenAISettings] = useState<AzureOpenAISettings | null>(null);
  const [tgiSettings, setTGISettings] = useState<TGISettings | null>(null);
  const [fastEmbedSettings, setFastEmbedSettings] = useState<FastEmbedSettings | null>(null);
  const [teiSettings, setTEISettings] = useState<TEISettings | null>(null);

  // UI states
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  const { getProviderSettings, updateProviderSettings } = useSettings();

  // Add loading state
  const [isLoading, setIsLoading] = useState(true);

  // Function to load provider settings
  const loadProviderSettings = async (provider: string) => {
    try {
      const response = await getProviderSettings(provider);
      if (!response) {
        console.warn(`No settings found for provider ${provider}`);
        return null;
      }

      const settings = response;
      console.log(" provider settings", settings);
      console.log("provider", provider);
      switch (provider) {
        case "ollama":
          setOllamaSettings(settings);
          break;
        case "openai":
          setOpenAISettings(settings);
          break;
        case "anthropic":
          setAnthropicSettings(settings);
          break;
        case "groq":
          setGroqSettings(settings);
          break;
        case "gemini":
          setGeminiSettings(settings);
          break;
        case "mistral":
          setMistralSettings(settings);
          break;
        case "azure-openai":
          setAzureOpenAISettings(settings);
          break;
        case "tgi":
          setTGISettings(settings);
          break;
        case "fastembed":
          setFastEmbedSettings(settings);
          break;
        case "tei":
          setTEISettings(settings);
          break;
      }
    } catch (error) {
      console.error(`Error loading ${provider} settings:`, error);
      setSaveError(`Failed to load ${provider} settings`);
    }
  };

  // Load settings when dialog opens
  useEffect(() => {
    let mounted = true;

    const initializeSettings = async () => {
      console.log("initializeSettings");
      if (!isOpen) return;
      setIsLoading(true);

      try {
        const appResponse = await getProviderSettings("app");
        console.log("appResponse", appResponse);
        if (!mounted || !appResponse) {
          setIsLoading(false);
          console.log("appResponse is null");
          return;
        }

        // Convert string values to numbers where needed
        const settings = {
          ...appResponse,
          embedding_dim: parseInt(appResponse.embedding_dim),
          top_k: parseInt(appResponse.top_k),
          max_iterations: parseInt(appResponse.max_iterations),
          temperature: parseFloat(appResponse.temperature)
        };

        setAppSettings(settings);

        console.log("settings", settings);

        // Load provider settings sequentially
        if (settings.llm_model_provider) {
          console.log("loading llm provider settings");
          await loadProviderSettings(settings.llm_model_provider);
          console.log("llm provider settings", ollamaSettings);
        }
        
        if (settings.embedding_model_provider && 
            settings.embedding_model_provider !== settings.llm_model_provider) {
          await loadProviderSettings(settings.embedding_model_provider);
        }

        if (mounted) {
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Error initializing settings:", error);
        setSaveError("Failed to load settings");
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    initializeSettings();

    return () => {
      mounted = false;
    };
  }, [isOpen, getProviderSettings]);

  // Handle provider change
  const handleProviderChange = async (type: 'llm' | 'embedding', newProvider: string) => {
    if (!appSettings) return;

    try {
      if (type === 'llm') {
        setAppSettings({ ...appSettings, llm_model_provider: newProvider });
        await loadProviderSettings(newProvider);
      } else {
        setAppSettings({ ...appSettings, embedding_model_provider: newProvider });
        if (newProvider !== appSettings.llm_model_provider) {
          await loadProviderSettings(newProvider);
        }
      }
    } catch (error) {
      console.error(`Error changing ${type} provider:`, error);
      setSaveError(`Failed to load ${newProvider} settings`);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);

    try {
      // Convert the settings object to a JSON string before sending
      if (!appSettings) return;

      await updateProviderSettings("app", appSettings);

      if (appSettings.llm_model_provider) {
        const llmSettings = getProviderSettingsState(appSettings.llm_model_provider);
        await updateProviderSettings(appSettings.llm_model_provider, llmSettings);
      }
      
      if (appSettings.embedding_model_provider && 
        appSettings.embedding_model_provider !== appSettings.llm_model_provider) {
        const embeddingSettings = getProviderSettingsState(appSettings.embedding_model_provider);
        await updateProviderSettings(appSettings.embedding_model_provider, embeddingSettings);
      }

      onClose();
    } catch (error) {
      console.error("Error saving settings:", error);
      setSaveError("Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  // Helper to get provider settings state
  const getProviderSettingsState = (provider: string) => {
    switch (provider) {
      case "ollama": return ollamaSettings;
      case "openai": return openAISettings;
      case "anthropic": return anthropicSettings;
      case "groq": return groqSettings;
      case "gemini": return geminiSettings;
      case "mistral": return mistralSettings;
      case "azure-openai": return azureOpenAISettings;
      case "tgi": return tgiSettings;
      case "fastembed": return fastEmbedSettings;
      case "tei": return teiSettings;
      default: return null;
    }
  };

  if (!isOpen) return null;

  // Show loading state
  if (isLoading || !appSettings) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }

  // Render the main dialog content only when appSettings is available
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
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

          <div className="space-y-2 relative">
            <label className="text-sm font-medium">LLM Model Provider</label>
            <Select
              value={appSettings.llm_model_provider}
              onValueChange={(value: string) => handleProviderChange('llm', value)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a model provider" />
              </SelectTrigger>
              <SelectContent className="z-[200]">
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

          {appSettings.llm_model_provider === "ollama" && ollamaSettings && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Ollama Host</label>
                <p className="text-xs text-gray-500">
                  Set to http://host.docker.internal:11434 if running locally
                </p>
                <Input
                  value={ollamaSettings.llm_host}
                  onChange={(e) => setOllamaSettings({
                    ...ollamaSettings,
                    llm_host: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <Select
                  value={isCustomModel("ollama", ollamaSettings.llm_model) ? "custom" : ollamaSettings.llm_model}
                  onValueChange={(value) => {
                    if (value === "custom") return;
                    setOllamaSettings({
                      ...ollamaSettings,
                      llm_model: value
                    });
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent className="z-[200]">
                    <SelectGroup>
                      {LLM_MODEL_OPTIONS["ollama"].map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
                {isCustomModel("ollama", ollamaSettings.llm_model) && (
                  <Input
                    className="mt-2"
                    placeholder="Enter custom model name"
                    value={ollamaSettings.llm_model === "custom" ? "" : ollamaSettings.llm_model}
                    onChange={(e) => setOllamaSettings({
                      ...ollamaSettings,
                      llm_model: e.target.value
                    })}
                  />
                )}
              </div>
            </>
          )}

          {appSettings.llm_model_provider === "openai" && openAISettings && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">OpenAI API Key</label>
                <Input
                  type="password"
                  value={openAISettings.api_key}
                  onChange={(e) => setOpenAISettings({
                    ...openAISettings,
                    api_key: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <Select
                  value={isCustomModel("openai", openAISettings.llm_model) ? "custom" : openAISettings.llm_model}
                  onValueChange={(value) => {
                    if (value === "custom") return;
                    setOpenAISettings({
                      ...openAISettings,
                      llm_model: value
                    });
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent className="z-[200]">
                    <SelectGroup>
                      {LLM_MODEL_OPTIONS["openai"].map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Model Provider</label>
            <Select
              value={appSettings.embedding_model_provider}
              onValueChange={(value: string) => handleProviderChange('embedding', value)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select an embedding provider" />
              </SelectTrigger>
              <SelectContent className="z-[200]">
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

          {appSettings.embedding_model_provider === "ollama" && ollamaSettings && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Ollama Embedding Host</label>
                <p className="text-xs text-gray-500">
                  Set to http://host.docker.internal:11434 if running locally
                </p>
                <Input
                  value={ollamaSettings.embedding_host}
                  onChange={(e) => setOllamaSettings({
                    ...ollamaSettings,
                    embedding_host: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Embedding Model</label>
                <Select
                  value={isCustomEmbeddingModel("ollama", ollamaSettings.embedding_model) ? "custom" : ollamaSettings.embedding_model}
                  onValueChange={(value) => {
                    if (value === "custom") return;
                    setOllamaSettings({
                      ...ollamaSettings,
                      embedding_model: value
                    });
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent className="z-[200]">
                    <SelectGroup>
                      {EMBEDDING_MODEL_OPTIONS["ollama"].map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
                {isCustomEmbeddingModel("ollama", ollamaSettings.embedding_model) && (
                  <Input
                    className="mt-2"
                    placeholder="Enter custom embedding model name"
                    value={ollamaSettings.embedding_model === "custom" ? "" : ollamaSettings.embedding_model}
                    onChange={(e) => setOllamaSettings({
                      ...ollamaSettings,
                      embedding_model: e.target.value
                    })}
                  />
                )}
              </div>
            </>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Dimensions</label>
            <Input
              value={appSettings.embedding_dim}
              onChange={(e) => setAppSettings({
                ...appSettings,
                embedding_dim: e.target.value
              })}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Top K Results</label>
            <Input
              type="number"
              value={appSettings.top_k}
              onChange={(e) => setAppSettings({
                ...appSettings,
                top_k: parseInt(e.target.value)
              })}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">System Prompt</label>
            <Textarea
              value={appSettings.system_prompt}
              onChange={(e) => setAppSettings({
                ...appSettings,
                system_prompt: e.target.value
              })}
              rows={4}
            />
          </div>

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