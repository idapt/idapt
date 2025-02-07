import { useEffect, useRef, useState, useCallback } from 'react';
import { useClientConfig } from '@/app/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';
import { withBackoff } from '@/app/lib/backoff';
import { getProcessingStatusRouteApiProcessingStatusGet, ProcessingStatusResponse } from '@/app/client';
import { useAuth } from '@/app/components/auth/auth-context';

export function useProcessingStatus() {
  const { backend } = useClientConfig();
  const { token } = useAuth();
  const client = useApiClient();
  const [status, setStatus] = useState<ProcessingStatusResponse | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef(false);

  const fetchInitialStatus = useCallback(async () => {
    if (!backend || !token || token === null) return;
    // TODO !
    const response = await getProcessingStatusRouteApiProcessingStatusGet({ client }); // query: { datasource_name: 'Files' } }); 
    const data = response.data;
    setStatus(data ?? null);
    return data;
  }, [backend, client]);

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
      const ws = new WebSocket(`${wsUrl}/api/processing/status/ws?token=${token}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStatus(data ?? null);
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