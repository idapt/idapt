"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Textarea } from "@/app/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { 
  AppSettings, 
  OllamaLLMSettings,
  OpenAILLMSettings,
  AnthropicLLMSettings,
  GroqLLMSettings,
  GeminiLLMSettings,
  MistralLLMSettings,
  AzureOpenAILLMSettings,
  TGILLMSettings,
  LLM_MODEL_PROVIDER_OPTIONS, 
  LLM_MODEL_OPTIONS, 
} from "@/app/types/settings";
import { useSettings } from "@/app/components/settings/settings-provider";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

// Helper function to check if a model is custom
const isCustomModel = (provider: string, modelName: string): boolean => {
  const predefinedModels = LLM_MODEL_OPTIONS[provider] || [];
  return !predefinedModels.includes(modelName) || modelName === "custom";
};

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  // Main app settings state
  const [appSettings, setAppSettings] = useState<AppSettings | null>(null);
  
  // Provider-specific settings states
  const [ollamaLLMSettings, setOllamaLLMSettings] = useState<OllamaLLMSettings | null>(null);
  const [openAILLMSettings, setOpenAILLMSettings] = useState<OpenAILLMSettings | null>(null);
  const [anthropicLLMSettings, setAnthropicLLMSettings] = useState<AnthropicLLMSettings | null>(null);
  const [groqLLMSettings, setGroqLLMSettings] = useState<GroqLLMSettings | null>(null);
  const [geminiLLMSettings, setGeminiLLMSettings] = useState<GeminiLLMSettings | null>(null);
  const [mistralLLMSettings, setMistralLLMSettings] = useState<MistralLLMSettings | null>(null);
  const [azureOpenAILLMSettings, setAzureOpenAILLMSettings] = useState<AzureOpenAILLMSettings | null>(null);
  const [tgiLLMSettings, setTGILLMSettings] = useState<TGILLMSettings | null>(null);

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

      switch (provider) {
        case "ollama_llm":
          setOllamaLLMSettings(settings);
          break;
        case "openai_llm":
          setOpenAILLMSettings(settings);
          break;
        case "anthropic_llm":
          setAnthropicLLMSettings(settings);
          break;
        case "groq_llm":
          setGroqLLMSettings(settings);
          break;
        case "gemini_llm":
          setGeminiLLMSettings(settings);
          break;
        case "mistral_llm":
          setMistralLLMSettings(settings);
          break;
        case "azure-openai_llm":
          setAzureOpenAILLMSettings(settings);
          break;
        case "tgi_llm":
          setTGILLMSettings(settings);
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
      if (!isOpen) return;
      setIsLoading(true);

      try {
        const appResponse = await getProviderSettings("app");
        if (!mounted || !appResponse) {
          setIsLoading(false);
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

        // Load provider settings sequentially
        if (settings.llm_model_provider) {
          await loadProviderSettings(settings.llm_model_provider);
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
  const handleProviderChange = async (newProvider: string) => {
    if (!appSettings) return;

    try {
      setAppSettings({ ...appSettings, llm_model_provider: newProvider });
      await loadProviderSettings(newProvider);
    } catch (error) {
      console.error(`Error changing provider:`, error);
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
      case "ollama_llm": return ollamaLLMSettings;
      case "openai_llm": return openAILLMSettings;
      case "anthropic_llm": return anthropicLLMSettings;
      case "groq_llm": return groqLLMSettings;
      case "gemini_llm": return geminiLLMSettings;
      case "mistral_llm": return mistralLLMSettings;
      case "azure-openai_llm": return azureOpenAILLMSettings;
      case "tgi_llm": return tgiLLMSettings;
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
              onValueChange={(value: string) => handleProviderChange(value)}
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

          {appSettings.llm_model_provider === "ollama_llm" && ollamaLLMSettings && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Ollama Host</label>
                <p className="text-xs text-gray-500">
                  Set to http://host.docker.internal:11434 if running locally
                </p>
                <Input
                  value={ollamaLLMSettings.host}
                  onChange={(e) => setOllamaLLMSettings({
                    ...ollamaLLMSettings,
                    host: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <Select
                  value={isCustomModel("ollama_llm", ollamaLLMSettings.model) ? "custom" : ollamaLLMSettings.model}
                  onValueChange={(value) => {
                    if (value === "custom") return;
                    setOllamaLLMSettings({
                      ...ollamaLLMSettings,
                      model: value
                    });
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent className="z-[200]">
                    <SelectGroup>
                      {LLM_MODEL_OPTIONS["ollama_llm"].map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
                {isCustomModel("ollama_llm", ollamaLLMSettings.model) && (
                  <Input
                    className="mt-2"
                    placeholder="Enter custom model name"
                    value={ollamaLLMSettings.model === "custom" ? "" : ollamaLLMSettings.model}
                    onChange={(e) => setOllamaLLMSettings({
                      ...ollamaLLMSettings,
                      model: e.target.value
                    })}
                  />
                )}
              </div>
            </>
          )}

          {appSettings.llm_model_provider === "openai_llm" && openAILLMSettings && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">OpenAI API Key</label>
                <Input
                  type="password"
                  value={openAILLMSettings.api_key}
                  onChange={(e) => setOpenAILLMSettings({
                    ...openAILLMSettings,
                    api_key: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <Select
                  value={isCustomModel("openai", openAILLMSettings.model) ? "custom" : openAILLMSettings.model}
                  onValueChange={(value) => {
                    if (value === "custom") return;
                    setOpenAILLMSettings({
                      ...openAILLMSettings,
                      model: value
                    });
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent className="z-[200]">
                    <SelectGroup>
                      {LLM_MODEL_OPTIONS["openai_llm"].map((model) => (
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