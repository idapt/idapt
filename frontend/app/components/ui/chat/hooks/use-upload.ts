import { useState, useRef } from 'react';
import { useClientConfig } from './use-config';
import { ConflictResolution, FileConflict } from "@/app/types/vault";
import { useProcessing } from '../../file-manager/hooks/use-processing';
import { uploadWithProgress } from '@/app/lib/upload-helpers';
import { useUser } from '@/app/contexts/user-context';

interface FileUploadItem {
  relative_path_from_home: string;
  base64_content: string;
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

    
  const uploadFile = async (
    uploadItem: FileUploadItem, 
    toastId: string, 
    onProgress: (id: string, progress: number) => void,
    onComplete: (id: string) => void
  ) => {
    try {
      setIsUploading(true);
      abortControllerRef.current = new AbortController();
      shouldCancelAllRef.current = false;
        
      setCurrentFile(uploadItem.name);

        try {
          const response = await uploadWithProgress({
            url: `${backend}/api/file-manager/upload-file`,
            data: uploadItem,
            signal: abortControllerRef.current.signal,
            onProgress: (progress: number) => onProgress(toastId, progress),
            userId
          });

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
    } finally {
      setIsUploading(false);
      setCurrentFile("");
    }
  };



  const uploadFiles = async (
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
          const response = await uploadWithProgress({
            url: `${backend}/api/file-manager/upload-files`,
            data: { items: [uploadItem] },
            signal: abortControllerRef.current.signal,
            onProgress: (progress: number) => onProgress(toastId, progress),
            userId
          });

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
    uploadFiles,
    uploadFile,
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
