'use client';

import { ToastProvider } from '@/app/contexts/toast-context';
import { ToastContainer } from '../toasts/toast-container';
import { StatusHandler } from './status-handler';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      {children}
      
      <ToastContainer />
    </ToastProvider>
  );
} 