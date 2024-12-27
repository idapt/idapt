'use client';

import { ToastProvider } from '@/app/contexts/toast-context';
import { ToastContainer } from '../ui/toasts/toast-container';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      {children}
      <ToastContainer />
    </ToastProvider>
  );
} 