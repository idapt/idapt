import { useApiClient } from '@/app/lib/api-client';
import { useUser } from '@/app/contexts/user-context';
import { useState } from 'react';
import {
  getAllSettingsRouteApiSettingsGet,
  createSettingRouteApiSettingsIdentifierPost,
  getSettingRouteApiSettingsIdentifierGet,
  updateSettingRouteApiSettingsIdentifierPatch,
  deleteSettingRouteApiSettingsIdentifierDelete,
  type SettingResponse
} from '@/app/client';

export function useSettingsAPI() {
  const [isLoading, setIsLoading] = useState(false);
  const client = useApiClient();
  const { userId } = useUser();

  const getAllSettings = async (): Promise<SettingResponse[]> => {
    try {
      const response = await getAllSettingsRouteApiSettingsGet({
        client,
        query: { user_id: userId }
      });
      return response.data?.data ?? [];
    } catch (error) {
      console.error('Error fetching settings:', error);
      return [];
    }
  };

  const getSetting = async (identifier: string): Promise<SettingResponse | null> => {
    try {
      const response = await getSettingRouteApiSettingsIdentifierGet({
        client,
        path: { identifier },
        query: { user_id: userId }
      });
      return response.data ?? null;
    } catch (error) {
      console.error(`Error fetching setting ${identifier}:`, error);
      return null;
    }
  };

  const createSetting = async (identifier: string, schema_identifier: string): Promise<void> => {
    setIsLoading(true);
    try {
      await createSettingRouteApiSettingsIdentifierPost({
        client,
        path: { identifier },
        query: { user_id: userId },
        body: { schema_identifier }
      });
    } catch (error) {
      console.error('Error creating setting:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const updateSetting = async (identifier: string, valuesToUpdate: Record<string, any>): Promise<void> => {
    setIsLoading(true);
    try {
      await updateSettingRouteApiSettingsIdentifierPatch({
        client,
        path: { identifier },
        query: { user_id: userId },
        body: { values_to_update_json: JSON.stringify(valuesToUpdate) }
      });
    } catch (error) {
      console.error('Error updating setting:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSetting = async (identifier: string): Promise<void> => {
    setIsLoading(true);
    try {
      await deleteSettingRouteApiSettingsIdentifierDelete({
        client,
        path: { identifier },
        query: { user_id: userId }
      });
    } catch (error) {
      console.error('Error deleting setting:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getAllSettings,
    getSetting,
    createSetting,
    updateSetting,
    deleteSetting,
    isLoading
  };
}