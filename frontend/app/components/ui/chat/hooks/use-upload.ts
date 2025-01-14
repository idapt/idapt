import { useState, useRef } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";
import { useProcessing } from '../../file-manager/hooks/use-processing';
import { uploadWithProgress } from '@/app/lib/upload-helpers';
import { useUser } from '@/app/contexts/user-context';

interface FileUploadItem {
  path: string;
  content: string;
  name: string;
  file_created_at: number;
  file_modified_at: number;
}

export function useUpload() {
  const { backend } = useClientConfig();
  const { process } = useProcessing();
  const { userId } = useUser();
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
            (progress: number) => onProgress(toastId, progress),
            userId
          );

          if (!response.ok) {
            throw new Error(`Failed to upload ${uploadItem.name}`);
          }

          // Trigger the file processing pipeline process with the uploaded file
          /*try {
            await process([{
              path: uploadItem.path,
              transformations_stack_name_list: ["sentence-splitter-512"]
            }]);
          } catch (error) {
            console.error('Failed to trigger generation:', error);
            // We don't throw here as we don't want to fail the upload if generation fails
          }*/
          
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
