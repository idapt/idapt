"use client";

import { AppSettings } from "../types/settings";
import { useClientConfig } from "../components/ui/chat/hooks/use-config";
import { useState, useCallback } from "react";
import { useApiClient } from "../lib/api-client";

export function useSettings() {
  const { backend } = useClientConfig();
  const [isLoading, setIsLoading] = useState(false);
  const { fetchWithAuth } = useApiClient();

  const getSettings = useCallback(async (): Promise<AppSettings> => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${backend}/api/settings`);
      if (!response.ok) {
        throw new Error("Failed to fetch settings");
      }
      return response.json();
    } finally {
      setIsLoading(false);
    }
  }, [backend]);

  const updateSettings = useCallback(async (settings: AppSettings): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${backend}/api/settings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw errorData;
      }
    } finally {
      setIsLoading(false);
    }
  }, [backend]);

  return {
    getSettings,
    updateSettings,
    isLoading
  };
} 