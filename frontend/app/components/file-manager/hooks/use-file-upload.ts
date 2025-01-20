import { useFiles } from './use-upload';
import { useUploadToast } from '@/app/components/toasts/hooks/use-upload-toast';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { uploadFileApi, isUploading } = useFiles();
  const { startUpload, updateUpload, completeUpload, failUpload } = useUploadToast();

  const uploadFile = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    let fileToastId: string | undefined;
    try {
      // Start upload toast
      fileToastId = startUpload(file.name, folderId ? `${folderId}/${file.name}` : file.name);

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
      await uploadFileApi(
        {
          original_path: folderId ? `${folderId}/${file.name}` : file.name,
          base64_content: base64_content,
          name: file.name,
          file_created_at: file.lastModified / 1000,
          file_modified_at: file.lastModified / 1000,
        }
      );

      completeUpload(fileToastId);
      options?.onComplete?.();
    } catch (error) {
      if (fileToastId) {
        failUpload(fileToastId);
      }
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFile,
    isUploading
  };
} 