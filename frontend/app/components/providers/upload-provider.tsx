'use client';

import { UploadProvider } from '@/app/contexts/upload-context';
import { ToastContainer } from '../ui/toasts/toast-container';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <UploadProvider>
      {children}
      <ToastContainer />
    </UploadProvider>
  );
} 