import { useUpload } from '../../chat/hooks/use-upload';
import { useUploadToast } from '@/app/hooks/use-upload-toast';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { uploadFile, currentFile, isUploading, cancelUpload } = useUpload();
  const { startUpload, updateUpload, completeUpload, failUpload } = useUploadToast();

  const uploadFileItem = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    let toastId: string | undefined;
    try {
      // Start upload toast
      toastId = startUpload(file.name, folderId ? `${folderId}/${file.name}` : file.name);

      // Read file content and create proper base64 with mime type
      const base64_content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => {
          const content = reader.result as string;
          // Get mime type from file
          const mimeType = file.type || 'application/octet-stream';
          // Format with proper mime type prefix
          resolve(`data:${mimeType};base64,${content.split(',')[1]}`);
        };
        reader.readAsDataURL(file);
      });

      // Upload file
      await uploadFile(
        {
          relative_path_from_home: folderId ? `${folderId}/${file.name}` : file.name,
          base64_content: base64_content,
          name: file.name,
          file_created_at: file.lastModified / 1000,
          file_modified_at: file.lastModified / 1000,
        },
        toastId,
        (id, progress) => updateUpload(id, progress),
        (id) => completeUpload(id)
      );
      
      options?.onComplete?.();
    } catch (error) {
      if (toastId) {
        failUpload(toastId);
      }
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFile: uploadFileItem,
    currentFile,
    isUploading,
    cancelUpload
  };
} 