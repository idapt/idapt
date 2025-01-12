import { useProcessingStatus } from '@/app/hooks/use-processing-status';
import { useOllamaStatus } from '@/app/hooks/use-ollama-status';

export function StatusHandler() {
  useProcessingStatus();
  useOllamaStatus();
  return null;
} 
