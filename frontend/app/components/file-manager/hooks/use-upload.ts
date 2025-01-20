import { useState, useRef, useCallback } from 'react';
import { useClientConfig } from '../../chat/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';

interface FileUploadItem {
  relative_path_from_home: string;
  base64_content: string;
  name: string;
  file_created_at: number;
  file_modified_at: number;
}

export function useFiles() {
  const { backend } = useClientConfig();
  const abortControllerRef = useRef<AbortController>();
  const shouldCancelAllRef = useRef(false);
  const [isUploading, setIsUploading] = useState(false);
  const { fetchWithAuth } = useApiClient();

  const cancelAllUploads = useCallback(() => {
    shouldCancelAllRef.current = true;
    abortControllerRef.current?.abort();
  }, []);
  
  const uploadFileApi = async (uploadItem: FileUploadItem) => {
    try {
      setIsUploading(true);
      
      // Create new abort controller for this upload
      abortControllerRef.current = new AbortController();
      
      // Check if we should cancel before starting
      if (shouldCancelAllRef.current) {
        throw new DOMException('Upload cancelled', 'AbortError');
      }

      const response = await fetchWithAuth(`${backend}/api/file-manager/upload-file`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(uploadItem),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Failed to upload ${uploadItem.name}`);
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw error; // Re-throw abort errors to handle them in the upload hook
      }
      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  return {
    uploadFileApi,
    isUploading,
    cancelAllUploads
  };
}
