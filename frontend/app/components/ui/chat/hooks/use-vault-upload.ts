import { useState } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";

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
  const [currentConflict, setCurrentConflict] = useState<FileConflict | null>(null);
  const [conflictResolution, setConflictResolution] = useState<ConflictResolution | null>(null);

  const uploadToVault = async (items: VaultUploadItem[], skipConflictCheck: boolean = false) => {
    try {
      if (!skipConflictCheck) {
        // First check for conflicts
        const conflictsResponse = await fetch(`${backend}/api/vault/check-conflicts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items }),
        });
        
        const conflicts = await conflictsResponse.json();
      }
      
      // Start upload with conflict resolution
      const response = await fetch(`${backend}/api/vault/upload${conflictResolution ? `?conflict_resolution=${conflictResolution}` : ''}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.event === 'conflict') {
                setCurrentConflict(JSON.parse(data.data));
                // Wait for user resolution
                await new Promise<void>((resolve) => {
                  const unsubscribe = watch(conflictResolution, (resolution) => {
                    if (resolution) {
                      unsubscribe();
                      resolve();
                    }
                  });
                });
                continue;
              }

              const progress: VaultUploadProgress = JSON.parse(data);
              setProgress(progress);

              if (progress.status === 'error') {
                throw new Error(progress.error || 'Upload failed');
              }

              if (progress.status === 'completed') {
                return;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
              continue;
            }
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
    currentConflict,
    resolveConflict: setConflictResolution,
  };
}
