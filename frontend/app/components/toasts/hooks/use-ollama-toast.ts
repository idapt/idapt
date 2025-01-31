import { useToastContext } from '@/app/contexts/toast-context';
import { OllamaToastItem } from '@/app/types/toast';

export function useOllamaToast() {
  const { addItems, removeItem } = useToastContext();
  
  const OLLAMA_TOAST_ID = 'ollama-download-status';

  const startDownloading = () => {
    // Remove any existing ollama toast first
    removeItem(OLLAMA_TOAST_ID);
    
    const item: OllamaToastItem = {
      id: OLLAMA_TOAST_ID,
      name: 'Ollama Status',
      path: '',
      status: 'pending',
      progress: 0,
      type: 'ollama'
    };
    addItems([item]);
  };

  const stopDownloading = () => {
    removeItem(OLLAMA_TOAST_ID);
  };

  return {
    startDownloading,
    stopDownloading
  };
} 