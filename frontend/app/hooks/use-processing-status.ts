import { useEffect } from 'react';
import { useProcessingToast } from './use-processing-toast';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';

export function useProcessingStatus() {
  const { backend } = useClientConfig();
  const { startProcessing, updateProcessing, completeProcessing, failProcessing } = useProcessingToast();

  useEffect(() => {
    const controller = new AbortController();
    let isProcessing = false;

    const checkStatus = async () => {
      try {
        const response = await fetch(`${backend}/api/generate/status`, {
          signal: controller.signal
        });
        
        const data = await response.json();
        const totalFiles = data.queued_count + data.processing_count + data.processed_count;
        
        if (totalFiles > 0) {
          if (!isProcessing) {
            startProcessing('Processing files', totalFiles);
            isProcessing = true;
          }
          updateProcessing('global-processing-status', data.processed_count, totalFiles);
        } else if (isProcessing) {
          completeProcessing('global-processing-status');
          isProcessing = false;
        }
      } catch (error) {
        if (isProcessing) {
          failProcessing('global-processing-status');
          isProcessing = false;
        }
      }
    };

    const interval = setInterval(checkStatus, 1000);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [backend, startProcessing, updateProcessing, completeProcessing, failProcessing]);
} 