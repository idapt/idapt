import { useState, useEffect, useRef } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";
import { decompressData } from '../../file-manager/utils/compression';
import { useUploadStore } from '@/app/stores/upload-store';

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

  const upload = async (items: FileUploadItem[], skipConflictCheck: boolean = false) => {
    try {
      setIsUploading(true);
      abortControllerRef.current = new AbortController();
      shouldCancelAllRef.current = false;

      // Add items to store
      useUploadStore.getState().addItems(
        items.map(item => ({
          name: item.name,
          path: item.path
        }))
      );

      // Upload files one by one
      for (let i = 0; i < items.length; i++) {
        if (shouldCancelAllRef.current) {
          break;
        }

        const item = items[i];
        const storeItem = useUploadStore.getState().items[i];
        
        useUploadStore.getState().updateItem(storeItem.id, {
          status: 'uploading',
          progress: 0
        });

        // Decompress current item
        const [header, base64Data] = item.content.split(',');
        const decompressedBase64 = decompressData(base64Data);
        const decompressedItem = {
          ...item,
          content: `${header},${decompressedBase64}`
        };

        const response = await fetch(`${backend}/api/file-manager/upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: [decompressedItem] }),
          signal: abortControllerRef.current.signal
        });

        if (!response.ok) {
          useUploadStore.getState().updateItem(storeItem.id, {
            status: 'error',
            progress: 0
          });
          throw new Error(`Failed to upload ${item.name}`);
        }

        useUploadStore.getState().updateItem(storeItem.id, {
          status: 'completed',
          progress: 100
        });
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Upload cancelled');
        useUploadStore.getState().cleanupPendingUploads();
        return;
      }
      console.error('Upload error:', error);
      useUploadStore.getState().cleanupPendingUploads();
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
