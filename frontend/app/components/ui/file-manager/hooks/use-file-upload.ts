import { useUpload } from '../../chat/hooks/use-upload';
import { useGenerate } from '../hooks/use-generate';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { upload, progress, currentConflict, resolveConflict } = useUpload();
  const { generate } = useGenerate();

  const uploadFile = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    const content = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsDataURL(file);
    });

    try {
      const filePath = folderId ? `${folderId}/${file.name}` : file.name;
      
      await upload([{
        path: filePath,
        content,
        is_folder: false,
        name: file.name,
        mime_type: file.type,
        original_created_at: file.lastModified.toString(),
        original_modified_at: file.lastModified.toString()
      }], true);

      // Add this file to the generate queue
      await generate([filePath]);
      
      options?.onComplete?.();
    } catch (error) {
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFile,
    progress,
    currentConflict,
    resolveConflict
  };
} 