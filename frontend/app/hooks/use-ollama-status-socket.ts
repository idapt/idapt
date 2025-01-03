import { useEffect, useRef } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';
import { useOllamaToast } from './use-ollama-toast';

export function useOllamaStatusSocket() {
  const { backend } = useClientConfig();
  const { startDownloading, stopDownloading } = useOllamaToast();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const isDownloadingRef = useRef(false);

  const handleStatus = (data: { is_downloading: boolean }) => {
    if (data.is_downloading && !isDownloadingRef.current) {
      isDownloadingRef.current = true;
      startDownloading();
    } else if (!data.is_downloading && isDownloadingRef.current) {
      isDownloadingRef.current = false;
      stopDownloading();
    }
  };

  const fetchInitialStatus = async () => {
    try {
      const response = await fetch(`${backend}/api/ollama-status`);
      const data = await response.json();
      handleStatus(data);
    } catch (error) {
      console.error('Failed to fetch initial status:', error);
    }
  };

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = backend?.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/api/ollama-status/ws`);
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
  }, [backend]);
}
