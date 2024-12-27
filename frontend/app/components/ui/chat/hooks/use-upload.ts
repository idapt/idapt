import { useState, useEffect, useRef } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";
import { useUploadContext } from '@/app/contexts/upload-context';

interface FileUploadItem {
  path: string;
  content: string;
  name: string;
  file_created_at: number;
  file_modified_at: number;
}

export function useUpload() {
  const { backend } = useClientConfig();
  const { addItems, updateItem } = useUploadContext();
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

  // Upload a list of files, server side function
  const upload = async (uploadItems: FileUploadItem[], skipConflictCheck: boolean = false) => {
    try {

      setIsUploading(true);
      abortControllerRef.current = new AbortController();
      shouldCancelAllRef.current = false;

      // Create context items with IDs before starting upload
      const contextItems = uploadItems.map(item => ({
        id: crypto.randomUUID(),
        name: item.name,
        path: item.path,
        status: 'pending' as const,
        progress: 0,
        _type: 'upload' as const
      }));

      // Add all items to context immediately to show pending state
      addItems(contextItems);

      // Upload files one by one
      for (let i = 0; i < uploadItems.length; i++) {
        // Check if the upload has been cancelled
        if (shouldCancelAllRef.current) {
          break;
        }

        // Get the file to upload and its corresponding context item
        const uploadItem = uploadItems[i];
        const contextItem = contextItems[i];
        // Set the current file name
        setCurrentFile(uploadItem.name);
        // Update the context item to indicate that it is uploading
        updateItem(contextItem.id, {
          status: 'uploading',
          progress: 0
        });

        // Try to upload the file
        try {
          // Send file to backend API
          const response = await uploadWithProgress(
            `${backend}/api/file-manager/upload`,
            { items: [uploadItem] },
            abortControllerRef.current.signal,
            (progress) => {
              updateItem(contextItem.id, { 
                status: 'uploading',
                progress 
              });
            }
          );

          // Check if the upload was successful
          if (!response.ok) {
            throw new Error(`Failed to upload ${uploadItem.name}`);
          }

          // Update the context item to indicate that it is completed
          updateItem(contextItem.id, {
            status: 'completed',
            progress: 100
          });

        } catch (error) {
          // Update the context item to indicate that there was an error
          updateItem(contextItem.id, {
            status: 'error',
            progress: 0
          });
          
          // If the error is an abort error, return
          if (error instanceof DOMException && error.name === 'AbortError') {
            return;
          }
          // Otherwise, throw the error
          throw error;
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    } finally {
      // Reset the upload status
      setIsUploading(false);
      // Reset the current file name
      setCurrentFile("");
      // Reset the abort controller
      abortControllerRef.current = null;
      // Reset the cancel all flag
      shouldCancelAllRef.current = false;
    }
  };

  return {
    upload,
    currentFile,
    isUploading,
    cancelUpload,
    currentConflict,
    resolveConflict
  };
}
