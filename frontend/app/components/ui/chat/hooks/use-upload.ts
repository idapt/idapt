import { useState, useEffect } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";
import { decompressData } from '../../file-manager/utils/compression';

interface FileUploadProgress {
  total: number;
  current: number;
  processed_items: string[];
  status: 'processing' | 'completed' | 'error';
  error?: string;
}

interface FileUploadItem {
  path: string;
  content: string;
  name: string;
  file_created_at: number;
  file_modified_at: number;
}

export function useUpload() {
  const { backend } = useClientConfig();
  const [progress, setProgress] = useState<FileUploadProgress | null>(null);
  const [currentConflict, setCurrentConflict] = useState<FileConflict | null>(null);
  const [conflictResolution, setConflictResolution] = useState<ConflictResolution | null>(null);

  const upload = async (items: FileUploadItem[], skipConflictCheck: boolean = false) => {
    try {
      // Decompress items before sending to backend
      const decompressedItems = items.map(item => {
        const [header, base64Data] = item.content.split(',');
        const decompressedBase64 = decompressData(base64Data);
        return {
          ...item,
          content: `${header},${decompressedBase64}`
        };
      });

      if (!skipConflictCheck) {
        // First check for conflicts
        const conflictsResponse = await fetch(`${backend}/api/file-manager/check-conflicts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: decompressedItems }),
        });
        
        const conflicts = await conflictsResponse.json();
      }
      
      // Start upload with conflict resolution
      const response = await fetch(`${backend}/api/file-manager/upload${conflictResolution ? `?conflict_resolution=${conflictResolution}` : ''}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: decompressedItems }),
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
          if (line.trim() === '') continue;
          
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6);
              const data = JSON.parse(jsonStr);
              
              if (data.event === 'conflict') {
                setCurrentConflict(JSON.parse(data.data));
                await new Promise<void>((resolve) => {
                  const checkResolution = () => {
                    if (conflictResolution) {
                      resolve();
                    }
                  };
                  
                  const interval = setInterval(checkResolution, 100);
                  return () => clearInterval(interval);
                });
                continue;
              }

              // Handle progress updates
              const progress: FileUploadProgress = data;
              setProgress(progress);

              if (progress.status === 'error') {
                throw new Error(progress.error || 'Upload failed');
              }

              if (progress.status === 'completed') {
                return;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
              if (e instanceof Error) throw e;
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
    upload,
    progress,
    currentConflict,
    resolveConflict: setConflictResolution,
  };
}
