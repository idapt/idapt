import { useEffect, useRef, useState, useCallback } from 'react';
import { useClientConfig } from '@/app/components/chat/hooks/use-config';
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
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (!backend) return;

    const wsUrl = backend.replace(/^http/, 'ws');
    const userId = localStorage.getItem('userId');
    const ws = new WebSocket(`${wsUrl}/api/processing/status/ws?user_id=${userId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
      errorCountRef.current = 0;
    };

    ws.onclose = () => {
      // Try to reconnect after 2 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      ws.close();
    };
  }, [backend]);

  const fetchInitialStatus = useCallback(async () => {
    try {
      const response = await fetchWithAuth(`${backend}/api/processing/status`, {
        signal: new AbortController().signal
      });
      
      if (!response.ok) {
        throw new Error(`Status response not ok: ${response.status}`);
      }
      
      const data = await response.json();
      setStatus(data);
      errorCountRef.current = 0;
    } catch (error) {
      errorCountRef.current++;
      if (errorCountRef.current > 3) {
        setStatus(null);
      }
    }
  }, [backend, fetchWithAuth]);

  useEffect(() => {
    // Fetch initial status then connect to WebSocket
    fetchInitialStatus().then(() => {
      connect();
    });

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect, fetchInitialStatus]);

  return { status };
} 

export default useProcessingStatus;