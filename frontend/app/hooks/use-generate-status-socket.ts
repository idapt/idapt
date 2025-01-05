import { useEffect, useRef } from 'react';
import { useProcessingToast } from './use-processing-toast';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';

export function useGenerateStatusSocket() {
  const { backend } = useClientConfig();
  const { startProcessing, updateProcessing, completeProcessing, failProcessing } = useProcessingToast();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const isProcessingRef = useRef(false);

  const handleStatus = (data: any) => {
    const totalFiles = data.queued_count + data.processing_count;
    const processedFiles = (data.processed_files?.length || 0);
    
    if (totalFiles > 0) {
      if (!isProcessingRef.current) {
        startProcessing('Processing files', totalFiles + processedFiles);
        isProcessingRef.current = true;
      }
      updateProcessing('global-processing-status', processedFiles, totalFiles + processedFiles);
    } else {
      if (isProcessingRef.current) {
        completeProcessing('global-processing-status');
        isProcessingRef.current = false;
      }
    }
  };

  const fetchInitialStatus = async () => {
    try {
      const response = await fetch(`${backend}/api/generate/status`);
      const data = await response.json();
      handleStatus(data);
    } catch (error) {
      console.error('Failed to fetch initial status:', error);
    }
  };

  const connect = () => {
    if (!backend || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = backend.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/api/generate/status/ws`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleStatus(data);
    };

    ws.onclose = () => {
      reconnectTimeoutRef.current = setTimeout(connect, 1000);
    };

    ws.onerror = () => {
      ws.close();
    };
  };

  useEffect(() => {
    // Fetch initial status before connecting to WebSocket
    //fetchInitialStatus().then(() => {
    //  connect();
    //});
    // For now just get the status every 1 second // TODO Reimplement websocket support
    const interval = setInterval(fetchInitialStatus, 1000);

    return () => {
      //if (reconnectTimeoutRef.current) {
      //  clearTimeout(reconnectTimeoutRef.current);
      //}
      //if (wsRef.current) {
      //  wsRef.current.close();
      //}
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [backend]);
} 