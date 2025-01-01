import { useGenerateStatusSocket } from '@/app/hooks/use-generate-status-socket';
import { useOllamaStatusSocket } from '@/app/hooks/use-ollama-status-socket';

export function StatusHandler() {
  useGenerateStatusSocket();
  useOllamaStatusSocket();
  return null;
} 