import { useClientConfig } from "../../chat/hooks/use-config";
import { useState } from "react";
import { useApiClient } from "@/app/lib/api-client";
export interface GenerateFile {
  path: string;
  transformations_stack_name_list?: string[];
}

export function useGenerate() {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const generate = async (files: GenerateFile[]) => {
    try {
        const response = await fetchWithAuth(`${backend}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ files }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate');
      }
      
      return data;
    } catch (error) {
      console.error('Generation error:', error);
      throw error;
    }
  };

  return { generate };
}

export default useGenerate;