import { useEffect, useState, useCallback, useRef } from 'react';
import { useClientConfig } from '@/app/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';
import { withBackoff } from '@/app/lib/backoff';
import { getOllamaStatusRouteApiOllamaStatusGet } from '@/app/client';
import { useAuth } from '@/app/components/auth/auth-context';

export function useOllamaStatus() {
  const { backend } = useClientConfig();
  const { token } = useAuth();
  const [isDownloading, setIsDownloading] = useState(false);
  const client = useApiClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef(false);

  const fetchInitialStatus = useCallback(async () => {
    if (!backend || !token || token === null) return;
    const response = await getOllamaStatusRouteApiOllamaStatusGet({ client });
    const data = response.data as { is_downloading: boolean };
    setIsDownloading(data.is_downloading);
    return data;
  }, [backend, client, token]);

  const connect = useCallback(async () => {
    if (!backend || isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      if (!token || token === null) {
        throw new Error('No token');
      }
      isConnectingRef.current = true;
      // First verify the backend is available with backoff
      await withBackoff(fetchInitialStatus);

      const wsUrl = backend.replace(/^http/, 'ws');
      const ws = new WebSocket(`${wsUrl}/api/ollama-status/ws?token=${token}`);
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
  }, [backend, fetchInitialStatus, token]);

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