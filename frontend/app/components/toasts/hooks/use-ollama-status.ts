import { useEffect, useState, useCallback, useRef } from 'react';
import { useClientConfig } from '@/app/components/chat/hooks/use-config';
import { useSettings } from "@/app/components/settings/hooks/use-settings";
import { useApiClient } from '@/app/lib/api-client';
import { withBackoff } from '@/app/lib/backoff';
//import { AppSettings } from '../types/settings';

export function useOllamaStatus() {
  const { backend } = useClientConfig();
  const [isDownloading, setIsDownloading] = useState(false);
  const { fetchWithAuth } = useApiClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef(false);

  const fetchInitialStatus = useCallback(async () => {
    if (!backend) return;
    const response = await fetchWithAuth(`${backend}/api/ollama-status`);
    const data = await response.json();
    setIsDownloading(data.is_downloading);
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
      const ws = new WebSocket(`${wsUrl}/api/ollama-status/ws?user_id=${userId}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setIsDownloading(data.is_downloading);
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

  return { isDownloading };
}

export default useOllamaStatus;