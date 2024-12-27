import { useToastContext } from '@/app/contexts/toast-context';
import { ProcessingToastItem } from '@/app/types/toast';

export function useProcessingToast() {
  const { addItems, updateItem, removeItem, items } = useToastContext();
  
  const PROCESSING_ID = 'global-processing-status';

  const startProcessing = (name: string, total: number) => {
    const existingItem = items.find(
      item => item.type === 'processing' && item.id === PROCESSING_ID
    );

    if (existingItem) {
      updateItem(PROCESSING_ID, {
        total,
        processed: 0,
        progress: 0
      } as ProcessingToastItem);
      return PROCESSING_ID;
    }

    const item: ProcessingToastItem = {
      id: PROCESSING_ID,
      name,
      path: '',
      status: 'processing',
      progress: 0,
      type: 'processing',
      total,
      processed: 0
    };
    addItems([item]);
    return PROCESSING_ID;
  };

  const updateProcessing = (id: string, processed: number, total: number) => {
    updateItem(id, {
      status: 'processing',
      progress: Math.round((processed / total) * 100),
      processed,
      total
    } as ProcessingToastItem);
  };

  const completeProcessing = (id: string) => {
    updateItem(id, {
      status: 'completed',
      progress: 100
    });
  };

  const failProcessing = (id: string) => {
    updateItem(id, {
      status: 'error',
      progress: 0
    });
  };

  return {
    startProcessing,
    updateProcessing,
    completeProcessing,
    failProcessing
  };
} 