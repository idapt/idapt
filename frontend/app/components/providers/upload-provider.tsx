'use client';

import { ToastProvider } from '@/app/contexts/toast-context';
import { ToastContainer } from '../ui/toasts/toast-container';
import { useProcessingStatus } from '@/app/hooks/use-processing-status';

function ProcessingStatusHandler() {
  useProcessingStatus();
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      {children}
      <ProcessingStatusHandler />
      <ToastContainer />
    </ToastProvider>
  );
} 