import { useToastContext } from '@/app/contexts/toast-context';
import { OllamaToastItem } from '@/app/types/toast';
import { useEffect } from 'react';

export function useOllamaToast() {
  const { addItems, removeItem } = useToastContext();
  
  const OLLAMA_TOAST_ID = 'ollama-download-status';

  const startDownloading = () => {
    const item: OllamaToastItem = {
      id: OLLAMA_TOAST_ID,
      name: '',
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