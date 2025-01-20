import { useProcessingStatus } from '@/app/components/toasts/hooks/use-processing-status';
import { useOllamaStatus } from '@/app/components/toasts/hooks/use-ollama-status';

export function StatusHandler() {
  useProcessingStatus();
  useOllamaStatus();
  return null;
} 
