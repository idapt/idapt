import { createContext, useContext, useState, useCallback } from 'react';
import { useProcessingStatus } from '@/app/components/toasts/hooks/use-processing-status';
import { useToastContext } from './toast-context';
import { ProcessingToastItem } from '@/app/types/toast';
import { ProcessingStatusResponse } from '@/app/client';

interface ProcessingContextType {
  status: ProcessingStatusResponse | null;
  showProcessingToast: () => void;
  hideProcessingToast: () => void;
  isToastVisible: boolean;
}

const ProcessingContext = createContext<ProcessingContextType | null>(null);

const PROCESSING_TOAST_ID = 'global-processing-status';

export function ProcessingProvider({ children }: { children: React.ReactNode }) {
  const { status } = useProcessingStatus();
  const { addItems, removeItem } = useToastContext();
  const [isToastVisible, setIsToastVisible] = useState(false);

  const showProcessingToast = useCallback(() => {
    const totalFiles = (status?.queued_count || 0) + (status?.processing_count || 0);
    const processedCount = (status?.processing_items?.filter(
      item => item.status === 'completed'
    ).length || 0) + (status?.queued_items?.filter(
      item => item.status === 'completed'
    ).length || 0);

    const item: ProcessingToastItem = {
      id: PROCESSING_TOAST_ID,
      name: 'Processing Files',
      path: '',
      status: 'processing',
      progress: totalFiles > 0 ? Math.round((processedCount / totalFiles) * 100) : 0,
      type: 'processing',
      total: totalFiles,
      processed: processedCount
    };
    addItems([item]);
    setIsToastVisible(true);
  }, [addItems, status]);

  const hideProcessingToast = useCallback(() => {
    removeItem(PROCESSING_TOAST_ID);
    setIsToastVisible(false);
  }, [removeItem]);

  return (
    <ProcessingContext.Provider value={{ 
      status,
      showProcessingToast, 
      hideProcessingToast,
      isToastVisible 
    }}>
      {children}
    </ProcessingContext.Provider>
  );
}

export function useProcessingContext() {
  const context = useContext(ProcessingContext);
  if (!context) {
    throw new Error('useProcessingContext must be used within a ProcessingProvider');
  }
  return context;
} 