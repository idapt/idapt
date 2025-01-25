import { useEffect, useRef, useState, useCallback } from 'react';
import { useClientConfig } from '@/app/components/chat/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';
import { withBackoff } from '@/app/lib/backoff';

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
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef(false);

  const fetchInitialStatus = useCallback(async () => {
    if (!backend) return;
    const response = await fetchWithAuth(`${backend}/api/processing/status`);
    if (!response.ok) {
      throw new Error(`Status response not ok: ${response.status}`);
    }
    const data = await response.json();
    setStatus(data);
    return data;
  }, [backend, fetchWithAuth]);

  const connect = useCallback(async () => {
    if (!backend || isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      isConnectingRef.current = true;
      // First verify the backend is available with backoff
      await withBackoff(fetchInitialStatus);

      const wsUrl = backend.replace(/^http/, 'ws');
      const userId = localStorage.getItem('userId');
      const ws = new WebSocket(`${wsUrl}/api/processing/status/ws?user_id=${userId}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStatus(data);
      };

      ws.onclose = () => {
        reconnectTimeoutRef.current = setTimeout(() => {
          isConnectingRef.current = false;
          connect();
        }, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch (error) {
      isConnectingRef.current = false;
    }
  }, [backend, fetchInitialStatus]);

  useEffect(() => {
    connect();

    return () => {
      isConnectingRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { status };
}

export default useProcessingStatus;