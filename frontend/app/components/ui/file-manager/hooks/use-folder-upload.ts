import { useUpload } from "../../chat/hooks/use-upload";
import { useGenerate } from "../hooks/use-generate";
import { useUploadContext } from '@/app/contexts/upload-context';

interface FolderUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFolderUpload() {
  const { upload, currentFile, isUploading, cancelUpload } = useUpload();

  const uploadFolder = async (folderInput: HTMLInputElement, targetPath: string = "", options?: FolderUploadOptions) => {
    if (!folderInput.files?.length) return;

    try {
      const files = Array.from(folderInput.files);
      
      // Create context items for all files before starting upload
      const contextItems = files.map(file => ({
        id: crypto.randomUUID(),
        name: file.name,
        path: targetPath ? `${targetPath}/${file.webkitRelativePath}` : file.webkitRelativePath,
        status: 'pending' as const,
        progress: 0
      }));

      // Prepare upload items
      const uploadItems = await Promise.all(files.map(async (file, index) => {
        const content = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        });

        return {
          path: contextItems[index].path,
          content,
          name: file.name,
          file_created_at: file.lastModified / 1000,
          file_modified_at: file.lastModified / 1000,
        };
      }));

      // Upload files
      await upload(uploadItems);
      
      options?.onComplete?.();
    } catch (error) {
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFolder,
    currentFile,
    isUploading,
    cancelUpload
  };
} 