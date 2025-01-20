import { useEffect, useState, useCallback, useRef } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';
import { useSettings } from "@/app/hooks/use-settings";
import { useApiClient } from '@/app/lib/api-client';
//import { AppSettings } from '../types/settings';

export function useOllamaStatus() {
  const { backend } = useClientConfig();
  const [isDownloading, setIsDownloading] = useState(false);
  const { getProviderSettings } = useSettings();
  const { fetchWithAuth } = useApiClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (!backend) return;

    const wsUrl = backend.replace(/^http/, 'ws');
    const userId = localStorage.getItem('userId');
    const ws = new WebSocket(`${wsUrl}/api/ollama-status/ws?user_id=${userId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setIsDownloading(data.is_downloading);
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
      const response = await fetchWithAuth(`${backend}/api/ollama-status`);
      const data = await response.json();
      setIsDownloading(data.is_downloading);
    } catch (error) {
      setIsDownloading(true);
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

  return { isDownloading };
}

export default useOllamaStatus;