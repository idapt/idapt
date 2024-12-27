import { useUpload } from '../../chat/hooks/use-upload';
import { useGenerate } from '../hooks/use-generate';
import { useUploadContext } from '@/app/contexts/upload-context';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { upload, currentFile, isUploading, cancelUpload } = useUpload();
  const { addItems } = useUploadContext();

  const uploadFile = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    try {
      // Create a context item before starting upload
      const contextItem = {
        id: crypto.randomUUID(),
        name: file.name,
        path: folderId ? `${folderId}/${file.name}` : file.name,
        status: 'pending' as const,
        progress: 0
      };
      
      addItems([contextItem]);

      // Read file content
      const content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      // Upload file
      await upload([{
        path: contextItem.path,
        content,
        name: file.name,
        file_created_at: file.lastModified / 1000,
        file_modified_at: file.lastModified / 1000,
      }]);
      
      options?.onComplete?.();
    } catch (error) {
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