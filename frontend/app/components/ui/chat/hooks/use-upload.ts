import { useState, useEffect, useRef } from 'react';
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
  const [currentFile, setCurrentFile] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [currentConflict, setCurrentConflict] = useState<FileConflict | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const resolveConflict = (resolution: ConflictResolution) => {
    setCurrentConflict(null);
    // Handle conflict resolution logic here
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

      // Upload files one by one
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        setCurrentFile(item.name);
        setProgress({
          total: items.length,
          current: i + 1,
          processed_items: [],
          status: 'processing'
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
          throw new Error(`Failed to upload ${item.name}`);
        }
      }

      setProgress({
        total: items.length,
        current: items.length,
        processed_items: items.map(i => i.path),
        status: 'completed'
      });

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Upload cancelled');
        return;
      }
      console.error('Upload error:', error);
      throw error;
    } finally {
      setIsUploading(false);
      setCurrentFile("");
      abortControllerRef.current = null;
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
