import { useEffect, useRef, useState } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';


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
  const { fetchWithAuth } = useApiClient();
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const errorCountRef = useRef(0);

  useEffect(() => {
    const controller = new AbortController();

    const fetchStatus = async () => {
      try {
        const response = await fetchWithAuth(`${backend}/api/processing/status`, {
          signal: controller.signal
        });
        
        if (!response.ok) {
          throw new Error(`Status response not ok: ${response.status}`);
        }
        
        const data = await response.json();
        setStatus(data);
        errorCountRef.current = 0; // Reset error count on success
      } catch (error) {
        errorCountRef.current++;
        //console.error(`Failed to fetch processing status (attempt ${errorCountRef.current}):`, error);
        if (errorCountRef.current > 3) {
          setStatus(null);
        }
      }
    };

    const interval = setInterval(fetchStatus, 2000);
    fetchStatus(); // Initial fetch

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [backend, fetchWithAuth]);

  return { status };
} 

export default useProcessingStatus;