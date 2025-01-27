"use client";

import { useClientConfig } from "@/app/components/chat/hooks/use-config";
import { useState, useCallback } from "react";
import { useApiClient } from "@/app/lib/api-client";
import { Setting } from "@/app/types/settings";

export function useSettingsAPI() {
  const { backend } = useClientConfig();
  const [isLoading, setIsLoading] = useState(false);
  const { fetchWithAuth } = useApiClient();

  const createSetting : (identifier: string, schema_identifier: string) => Promise<void> = useCallback(async (identifier: string, schema_identifier: string) => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${backend}/api/settings/${identifier}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // SettingCreateRequest
        body: JSON.stringify({
          schema_identifier: schema_identifier,
        }),
      });
      if (!response.ok) {
        throw new Error(`Failed to create settings`);
      }
    } catch (error) {
      console.error(`Error creating settings:`, error);
    } finally {
      setIsLoading(false);
    }
  }, [backend, fetchWithAuth]);

  const getAllSettings : () => Promise<Setting[]> = useCallback(async () => {
    try {
      const response = await fetchWithAuth(`${backend}/api/settings`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch all settings`);
      }
      const settingsResponse : Setting[] = await response.json();
      return settingsResponse;
    } catch (error) {
      console.error(`Error fetching all settings:`, error);
      return [];
    }
  }, [backend, fetchWithAuth]);

  const getSetting : (identifier: string) => Promise<Setting | null> = useCallback(async (identifier: string) => {
    try {
      const response = await fetchWithAuth(`${backend}/api/settings/${identifier}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${identifier} settings`);
      }
      const settingsResponse : Setting = await response.json();
      return settingsResponse;
    } catch (error) {
      console.error(`Error fetching ${identifier} settings:`, error);
      return null;
    }
  }, [backend, fetchWithAuth]);

  const updateSetting : (identifier: string, valuesToUpdate: Record<string, any>) => Promise<void> = useCallback(async (identifier: string, valuesToUpdate: Record<string, any>) => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${backend}/api/settings/${identifier}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          values_to_update_json: JSON.stringify(valuesToUpdate)
        }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update setting');
      }
    } finally {
      setIsLoading(false);
    }
  }, [backend, fetchWithAuth]);

  const deleteSetting : (identifier: string) => Promise<void> = useCallback(async (identifier: string) => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${backend}/api/settings/${identifier}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error(`Failed to delete ${identifier} settings`);
      }
    } catch (error) {
      console.error(`Error deleting ${identifier} settings:`, error);
    } finally {
      setIsLoading(false);
    }
  }, [backend, fetchWithAuth]);

  return { createSetting, getAllSettings, getSetting, updateSetting, deleteSetting, isLoading };
} 