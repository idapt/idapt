import { useEffect, useState } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';
import { useSettings } from "@/app/hooks/use-settings";
import { useApiClient } from '@/app/lib/api-client';
export function useOllamaStatus() {
  const { backend } = useClientConfig();
  const [isDownloading, setIsDownloading] = useState(false);
  const { getSettings } = useSettings();
  const { fetchWithAuth } = useApiClient();

  useEffect(() => {
    const abortController = new AbortController();
    const checkStatus = async () => {
      try {
        const appSettings = await getSettings();
        // If the app settings embed model provider and llm model provider are both not set to ollama, we don't need to check the ollama status
        if (appSettings.embedding_model_provider !== 'ollama' && appSettings.llm_model_provider !== 'ollama') {
          setIsDownloading(false);
          return;
        }

        const response = await fetchWithAuth(`${backend}/api/ollama-status`, { signal: abortController.signal });
        const data = await response.json();
        const isDownloading = data.is_downloading;
        setIsDownloading(isDownloading);
      } catch (error) {
        //console.error('Failed to fetch ollama status:', error);
        // By default, we set isDownloading to true to show the processing toast
        setIsDownloading(true);
      }
    };

    const interval = setInterval(checkStatus, 2000);
    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, [backend, getSettings, fetchWithAuth]);

  return { isDownloading };
}

export default useOllamaStatus;