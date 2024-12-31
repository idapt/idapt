'use client';

import { ToastProvider } from '@/app/contexts/toast-context';
import { ToastContainer } from '../ui/toasts/toast-container';
import { useGenerateStatusSocket } from '@/app/hooks/use-generate-status-socket';

function ProcessingStatusHandler() {
  useGenerateStatusSocket();
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