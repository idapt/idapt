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
    const processFiles: ProcessingFile[] = files.map(path => ({
      path,
      transformations_stack_name_list: [stackIdentifier]
    }));

    return process(processFiles);
  };

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

  const processFolder = async (folderPath: string, stackIdentifier: string) => {
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
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process folder');
      }
      
      return data;
    } catch (error) {
      console.error('Processing folder error:', error);
      throw error;
    }
  };

  return { process, processWithStack, processFolder };
}

export default useProcessing;