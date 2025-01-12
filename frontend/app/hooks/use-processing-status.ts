import { useEffect, useRef, useState } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';



interface ProcessingFile {
  name: string;
  path: string;
}

interface ProcessingStatus {
  queued_count: number;
  processing_count: number;
  queued_files: ProcessingFile[];
  processing_files: ProcessingFile[];
}

export function useProcessingStatus() {
  const { backend } = useClientConfig();
  const [status, setStatus] = useState<ProcessingStatus | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchStatus = async () => {
      try {
        const response = await fetch(`${backend}/api/generate/status`, {
          signal: controller.signal
        });
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch processing status:', error);
        setStatus(null);
      }
    };

    const interval = setInterval(fetchStatus, 2000);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [backend]);

  return { status };
} 

export default useProcessingStatus;