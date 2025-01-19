"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../dialog";
import { Input } from "../input";
import { Button } from "../button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../select";
import { useClientConfig } from "../chat/hooks/use-config";
import { useApiClient } from "@/app/lib/api-client";
import { 
  EMBEDDING_PROVIDER_OPTIONS, 
  EMBEDDING_MODEL_OPTIONS
} from "@/app/types/settings";
import { Textarea } from "../textarea";

interface CreateDatasourceDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

// Helper function to check if a model is custom
export const isCustomModel = (provider: string, modelName: string): boolean => {
  const predefinedModels = EMBEDDING_MODEL_OPTIONS[provider as keyof typeof EMBEDDING_MODEL_OPTIONS] || [];
  return !predefinedModels.includes(modelName) || modelName === "custom";
};

export function CreateDatasourceDialog({ open, onClose, onCreated }: CreateDatasourceDialogProps) {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [embeddingProvider, setEmbeddingProvider] = useState("ollama_embed");
  const [embeddingModel, setEmbeddingModel] = useState(EMBEDDING_MODEL_OPTIONS.ollama_embed[0]);
  const [customModel, setCustomModel] = useState("");
  const [ollamaHost, setOllamaHost] = useState("http://host.docker.internal:11434");
  const [openAIKey, setOpenAIKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) return;

    try {
      setLoading(true);
      setError(null);

      let embeddingSettings;
      const selectedModel = customModel || embeddingModel;

      switch (embeddingProvider) {
        case "ollama_embed":
          embeddingSettings = {
            identifier: "ollama_embed",
            display_name: "Ollama Embeddings",
            description: "Ollama embedding provider settings",
            model: selectedModel,
            host: ollamaHost,
            request_timeout: 60
          };
          break;
        case "openai_embed":
          embeddingSettings = {
            identifier: "openai_embed",
            display_name: "OpenAI Embeddings",
            description: "OpenAI embedding provider settings",
            model: selectedModel,
            api_key: openAIKey
          };
          break;
        default:
          throw new Error(`Unsupported embedding provider: ${embeddingProvider}`);
      }

      const response = await fetchWithAuth(`${backend}/api/datasources`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          description: description,
          type: 'files',
          settings: {},
          embedding_provider: embeddingProvider,
          embedding_settings: embeddingSettings
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create datasource');
      }

      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create datasource');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Datasource</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter datasource name"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter datasource description"
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Provider</label>
            <Select
              value={embeddingProvider}
              onValueChange={setEmbeddingProvider}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select embedding provider" />
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
              value={isCustomModel(embeddingProvider, embeddingModel) ? "custom" : embeddingModel}
              onValueChange={(value) => {
                if (value === "custom") {
                  setEmbeddingModel("custom");
                } else {
                  setEmbeddingModel(value);
                  setCustomModel("");
                }
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select embedding model" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {EMBEDDING_MODEL_OPTIONS[embeddingProvider].map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>

            {isCustomModel(embeddingProvider, embeddingModel) && (
              <Input
                className="mt-2"
                placeholder="Enter custom model name"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
              />
            )}
          </div>

          {embeddingProvider === "ollama_embed" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Ollama Host</label>
              <Input
                value={ollamaHost}
                onChange={(e) => setOllamaHost(e.target.value)}
                placeholder="Enter Ollama host URL"
              />
            </div>
          )}

          {embeddingProvider === "openai_embed" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">OpenAI API Key</label>
              <Input
                type="password"
                value={openAIKey}
                onChange={(e) => setOpenAIKey(e.target.value)}
                placeholder="Enter OpenAI API key"
              />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-500 mt-1">{error}</p>
          )}

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={loading}>
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 