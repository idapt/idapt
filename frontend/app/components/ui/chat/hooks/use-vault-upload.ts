import { useState } from 'react';
import { useClientConfig } from './use-config';

interface VaultUploadProgress {
  total: number;
  current: number;
  processed_items: string[];
  status: 'processing' | 'completed' | 'error';
  error?: string;
}

interface VaultUploadItem {
  path: string;
  content: string;
  is_folder: boolean;
  name: string;
}

export function useVaultUpload() {
  const { backend } = useClientConfig();
  const [progress, setProgress] = useState<VaultUploadProgress | null>(null);

  const uploadToVault = async (items: VaultUploadItem[]) => {
    try {
      const response = await fetch(`${backend}/api/vault/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items }),
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response reader');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Parse SSE data
        const text = new TextDecoder().decode(value);
        const data = text.split('\n')
          .find(line => line.startsWith('data: '))
          ?.replace('data: ', '');

        if (data) {
          const progress: VaultUploadProgress = JSON.parse(data);
          setProgress(progress);

          if (progress.status === 'error' || progress.status === 'completed') {
            break;
          }
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  };

  return {
    uploadToVault,
    progress,
  };
}
