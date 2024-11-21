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
import { AppSettings, MODEL_PROVIDER_OPTIONS } from "@/app/types/settings";
import { getSettings, updateSettings } from "@/app/api/settings";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      getSettings()
        .then(setSettings)
        .catch(error => setError(error.message));
    }
  }, [isOpen]);

  const handleSave = async () => {
    if (!settings) return;
    
    try {
      setError(null);
      setIsSaving(true);
      await updateSettings(settings);
      onClose();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      setError(`Failed to update settings: ${errorMessage}`);
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
          {error && (
            <div className="text-red-500 text-sm">{error}</div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Model Provider</label>
            <Select
              value={settings.model_provider}
              onValueChange={(value) => setSettings({...settings, model_provider: value})}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a model provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {MODEL_PROVIDER_OPTIONS.map((provider) => (
                    <SelectItem key={provider} value={provider}>
                      {provider}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          {/* Only show the custom ollama host input if the model provider is custom_ollama */}
          {settings.model_provider === "custom_ollama" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Custom Ollama Host</label>
              <Input
                value={settings.custom_ollama_host}
                onChange={(e) => setSettings({...settings, custom_ollama_host: e.target.value})}
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Model</label>
            <Input
              value={settings.model}
              onChange={(e) => setSettings({...settings, model: e.target.value})}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding Model</label>
            <Input
              value={settings.embedding_model}
              onChange={(e) => setSettings({...settings, embedding_model: e.target.value})}
            />
          </div>

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
          {(settings.model_provider === "integrated_ollama" || settings.model_provider === "custom_ollama") && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Ollama Request Timeout (s)</label>
              <Input
                type="number"
                value={settings.ollama_request_timeout}
                onChange={(e) => setSettings({...settings, ollama_request_timeout: parseInt(e.target.value)})}
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