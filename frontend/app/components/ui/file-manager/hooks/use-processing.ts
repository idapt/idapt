import { useClientConfig } from "../../chat/hooks/use-config";
import { useApiClient } from "@/app/lib/api-client";
export interface ProcessingFile {
  path: string;
  transformations_stack_name_list?: string[];
}

export function useProcessing() {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const process = async (files: ProcessingFile[]) => {
    try {
        const response = await fetchWithAuth(`${backend}/api/processing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ files }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process');
      }
      
      return data;
    } catch (error) {
      console.error('Processing error:', error);
      throw error;
    }
  };

  return { process };
}

export default useProcessing;