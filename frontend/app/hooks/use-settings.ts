"use client";

import { AppSettings } from "../types/settings";
import { useClientConfig } from "../components/ui/chat/hooks/use-config";
import { useState, useCallback } from "react";
import { useApiClient } from "../lib/api-client";

export function useSettings() {
  const { backend } = useClientConfig();
  const [isLoading, setIsLoading] = useState(false);
  const { fetchWithAuth } = useApiClient();

  const getProviderSettings = useCallback(async (provider: string) => {
    try {
      const response = await fetchWithAuth(`${backend}/api/settings/${provider}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${provider} settings`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching ${provider} settings:`, error);
      return null;
    }
  }, [backend, fetchWithAuth]);

  const updateProviderSettings = useCallback(async (provider: string, settings: any) => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${backend}/api/settings/${provider}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ json_setting_object_str: JSON.stringify(settings) }),
      });
      if (!response.ok) {
        throw await response.json();
      }
    } finally {
      setIsLoading(false);
    }
  }, [backend, fetchWithAuth]);

  return { getProviderSettings, updateProviderSettings, isLoading };
} 