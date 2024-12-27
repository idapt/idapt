import { useState, useEffect, useRef } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";

interface FileUploadItem {
  path: string;
  content: string;
  name: string;
  file_created_at: number;
  file_modified_at: number;
}

export function useUpload() {
  const { backend } = useClientConfig();
  const abortControllerRef = useRef<AbortController>();
  const shouldCancelAllRef = useRef(false);
  const [currentFile, setCurrentFile] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const upload = async (
    uploadItems: FileUploadItem[], 
    toastIds: string[], 
    onProgress: (id: string, progress: number) => void,
    onComplete: (id: string) => void
  ) => {
    try {
      setIsUploading(true);
      abortControllerRef.current = new AbortController();
      shouldCancelAllRef.current = false;

      // Upload files one by one
      for (let i = 0; i < uploadItems.length; i++) {
        if (shouldCancelAllRef.current) break;

        const uploadItem = uploadItems[i];
        const toastId = toastIds[i];
        
        setCurrentFile(uploadItem.name);

        try {
          const response = await uploadWithProgress(
            `${backend}/api/file-manager/upload`,
            { items: [uploadItem] },
            abortControllerRef.current.signal,
            (progress: number) => onProgress(toastId, progress)
          );

          if (!response.ok) {
            throw new Error(`Failed to upload ${uploadItem.name}`);
          }
          
          // Mark file as completed after successful upload
          onComplete(toastId);
        } catch (error) {
          if (error instanceof DOMException && error.name === 'AbortError') {
            return;
          }
          throw error;
        }
      }
    } finally {
      setIsUploading(false);
      setCurrentFile("");
    }
  };

  return {
    upload,
    currentFile,
    isUploading,
    cancelUpload: () => {
      abortControllerRef.current?.abort();
      shouldCancelAllRef.current = true;
      setIsUploading(false);
      setCurrentFile("");
    }
  };
}

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

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(new Response(xhr.response, {
          status: xhr.status,
          headers: { 'Content-Type': 'application/json' }
        }));
      } else {
        reject(new Error(`HTTP ${xhr.status}`));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Network error')));
    xhr.addEventListener('abort', () => reject(new DOMException('The user aborted a request.', 'AbortError')));

    signal.addEventListener('abort', () => xhr.abort());

    xhr.send(JSON.stringify(data));
  });
};
