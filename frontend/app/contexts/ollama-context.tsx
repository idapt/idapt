import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useOllamaStatus } from '@/app/components/toasts/hooks/use-ollama-status';
import { useToastContext } from './toast-context';
import { OllamaToastItem } from '@/app/types/toast';

interface OllamaContextType {
  isDownloading: boolean;
  showOllamaToast: () => void;
  hideOllamaToast: () => void;
  isToastVisible: boolean;
}

const OllamaContext = createContext<OllamaContextType | null>(null);

const OLLAMA_TOAST_ID = 'ollama-status';

export function OllamaProvider({ children }: { children: React.ReactNode }) {
  const { isDownloading } = useOllamaStatus();
  const { addItems, removeItem } = useToastContext();
  const [isToastVisible, setIsToastVisible] = useState(false);

  const showOllamaToast = useCallback(() => {
    const item: OllamaToastItem = {
      id: OLLAMA_TOAST_ID,
      name: 'Ollama Status',
      path: '',
      status: 'pending',
      progress: 0,
      type: 'ollama'
    };
    addItems([item]);
    setIsToastVisible(true);
  }, [addItems]);

  const hideOllamaToast = useCallback(() => {
    removeItem(OLLAMA_TOAST_ID);
    setIsToastVisible(false);
  }, [removeItem]);

  return (
    <OllamaContext.Provider value={{ 
      isDownloading, 
      showOllamaToast, 
      hideOllamaToast, 
      isToastVisible 
    }}>
      {children}
    </OllamaContext.Provider>
  );
}

export function useOllamaContext() {
  const context = useContext(OllamaContext);
  if (!context) {
    throw new Error('useOllamaContext must be used within an OllamaProvider');
  }
  return context;
} 