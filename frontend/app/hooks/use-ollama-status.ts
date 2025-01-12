import { useEffect, useState } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';
import { useSettings } from "@/app/hooks/use-settings";

export function useOllamaStatus() {
  const { backend } = useClientConfig();
  const [isDownloading, setIsDownloading] = useState(false);
  const abortController = new AbortController();
  const { getSettings } = useSettings();

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const appSettings = await getSettings();
        // If the app settings embed model provider and llm model provider are both not set to ollama, we don't need to check the ollama status
        if (appSettings.embedding_model_provider !== 'ollama' && appSettings.llm_model_provider !== 'ollama') {
          setIsDownloading(false);
          return;
        }

        const response = await fetch(`${backend}/api/ollama-status`, { signal: abortController.signal });
        const data = await response.json();
        const isDownloading = data.is_downloading;
        setIsDownloading(isDownloading);
      } catch (error) {
        console.error('Failed to fetch ollama status:', error);
        // By default, we set isDownloading to true to show the processing toast
        setIsDownloading(true);
      }
    };

    const interval = setInterval(checkStatus, 2000);
    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, [backend, getSettings]);

  return { isDownloading };
}

export default useOllamaStatus;