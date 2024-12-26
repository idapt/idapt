import { useState, useEffect, useRef } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";
import { decompressData } from '../../file-manager/utils/compression';
import { useUploadContext } from '@/app/contexts/upload-context';

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
  const { addItems, updateItem, items, cancelAll } = useUploadContext();
  const [progress, setProgress] = useState<FileUploadProgress | null>(null);
  const [currentFile, setCurrentFile] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [currentConflict, setCurrentConflict] = useState<FileConflict | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const shouldCancelAllRef = useRef(false);

  useEffect(() => {
    const handleCancelAll = () => {
      shouldCancelAllRef.current = true;
      abortControllerRef.current?.abort();
    };

    window.addEventListener('cancelAllUploads', handleCancelAll);
    return () => window.removeEventListener('cancelAllUploads', handleCancelAll);
  }, []);

  const resolveConflict = (resolution: ConflictResolution) => {
    setCurrentConflict(null);
  };

  const cancelUpload = () => {
    abortControllerRef.current?.abort();
    setIsUploading(false);
    setProgress(null);
    setCurrentFile("");
  };

  const uploadWithProgress = (
    url: string, 
    data: any, 
    signal: AbortSignal,
    onProgress: (progress: number) => void
  ): Promise<Response> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.responseType = 'json';

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(new Response(JSON.stringify(xhr.response), {
            status: xhr.status,
            headers: { 'Content-Type': 'application/json' }
          }));
        } else {
          reject(new Error(`HTTP ${xhr.status} - ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Network error')));
      xhr.addEventListener('abort', () => reject(new DOMException('The user aborted a request.', 'AbortError')));

      signal.addEventListener('abort', () => xhr.abort());

      xhr.send(JSON.stringify(data));
    });
  };

  const upload = async (uploadItems: FileUploadItem[], skipConflictCheck: boolean = false) => {
    try {
      setIsUploading(true);
      abortControllerRef.current = new AbortController();
      shouldCancelAllRef.current = false;

      // Create context items with IDs before adding them
      const contextItems = uploadItems.map(item => ({
        id: crypto.randomUUID(),
        name: item.name,
        path: item.path,
        status: 'pending' as const,
        progress: 0
      }));

      // Add items to context with their IDs
      addItems(contextItems);

      for (let i = 0; i < uploadItems.length; i++) {
        if (shouldCancelAllRef.current) {
          break;
        }

        const uploadItem = uploadItems[i];
        const contextItem = contextItems[i];
        setCurrentFile(uploadItem.name);
        
        updateItem(contextItem.id, {
          status: 'uploading',
          progress: 0
        });

        try {
          // Decompress current item
          const [header, base64Data] = uploadItem.content.split(',');
          const decompressedBase64 = decompressData(base64Data);
          const decompressedItem = {
            ...uploadItem,
            content: `${header},${decompressedBase64}`
          };

          const response = await uploadWithProgress(
            `${backend}/api/file-manager/upload`,
            { items: [decompressedItem] },
            abortControllerRef.current.signal,
            (progress) => {
              updateItem(contextItem.id, { 
                status: 'uploading',
                progress 
              });
            }
          );

          if (!response.ok) {
            throw new Error(`Failed to upload ${uploadItem.name}`);
          }

          updateItem(contextItem.id, {
            status: 'completed',
            progress: 100
          });

        } catch (error) {
          updateItem(contextItem.id, {
            status: 'error',
            progress: 0
          });
          
          if (error instanceof DOMException && error.name === 'AbortError') {
            return;
          }
          throw error;
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    } finally {
      setIsUploading(false);
      setCurrentFile("");
      abortControllerRef.current = null;
      shouldCancelAllRef.current = false;
    }
  };

  return {
    upload,
    progress,
    currentFile,
    isUploading,
    cancelUpload,
    currentConflict,
    resolveConflict
  };
}
