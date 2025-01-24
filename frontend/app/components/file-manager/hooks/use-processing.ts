import { useClientConfig } from "@/app/components/chat/hooks/use-config";
import { useApiClient } from "@/app/lib/api-client";

export interface ProcessingFile {
  original_path: string;
  stacks_identifiers_to_queue?: string[];
}

export function useProcessing() {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const processWithStack = async (files: string[], stackIdentifier: string) => {
    const controller = new AbortController();
    try {
      const processFiles: ProcessingFile[] = files.map(original_path => ({
        original_path,
        stacks_identifiers_to_queue: [stackIdentifier]
      }));

      const response = await fetchWithAuth(`${backend}/api/processing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: processFiles }),
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
      const response = await fetchWithAuth(`${backend}/api/processing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: [{
            original_path: folderPath,
            stacks_identifiers_to_queue: [stackIdentifier]
          }]
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