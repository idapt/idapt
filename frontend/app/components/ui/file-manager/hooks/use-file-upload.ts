import { useUpload } from '../../chat/hooks/use-upload';
import { useUploadToast } from '@/app/hooks/use-upload-toast';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { upload, currentFile, isUploading, cancelUpload } = useUpload();
  const { startUpload, updateUpload, completeUpload, failUpload } = useUploadToast();

  const uploadFile = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    let toastId: string | undefined;
    try {
      // Start upload toast
      toastId = startUpload(file.name, folderId ? `${folderId}/${file.name}` : file.name);

      // Read file content
      const content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      // Upload file
      await upload(
        [{
          path: folderId ? `${folderId}/${file.name}` : file.name,
          content,
          name: file.name,
          file_created_at: file.lastModified / 1000,
          file_modified_at: file.lastModified / 1000,
        }], 
        [toastId],
        (id, progress) => updateUpload(id, progress)
      );
      
      completeUpload(toastId);
      options?.onComplete?.();
    } catch (error) {
      if (toastId) {
        failUpload(toastId);
      }
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFile,
    currentFile,
    isUploading,
    cancelUpload
  };
} 