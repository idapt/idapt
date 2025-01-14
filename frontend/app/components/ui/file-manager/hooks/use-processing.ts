import { useClientConfig } from "../../chat/hooks/use-config";
import { useApiClient } from "@/app/lib/api-client";

export interface ProcessingFile {
  path: string;
  transformations_stack_name_list?: string[];
}

export function useProcessing() {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const processWithStack = async (files: string[], stackIdentifier: string) => {
    const controller = new AbortController();
    try {
      const processFiles: ProcessingFile[] = files.map(path => ({
        path,
        transformations_stack_name_list: [stackIdentifier]
      }));

      const response = await fetchWithAuth(`${backend}/api/processing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ files: processFiles }),
        signal: controller.signal
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process');
      }
      
      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Processing error:', error);
      throw error;
    } finally {
      controller.abort();
    }
  };

  const processFolder = async (folderPath: string, stackIdentifier: string) => {
    const controller = new AbortController();
    try {
      const response = await fetchWithAuth(`${backend}/api/processing/folder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          folder_path: folderPath,
          transformations_stack_name_list: [stackIdentifier]
        }),
        signal: controller.signal
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process folder');
      }
      
      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Processing folder error:', error);
      throw error;
    } finally {
      controller.abort();
    }
  };

  return { processWithStack, process, processFolder };
}

export default useProcessing;