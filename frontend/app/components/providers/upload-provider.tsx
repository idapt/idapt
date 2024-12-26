'use client';

import { UploadProvider } from '@/app/contexts/upload-context';
import { UploadToast } from '../ui/file-manager/upload-toast';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <UploadProvider>
      {children}
      <UploadToast />
    </UploadProvider>
  );
} 