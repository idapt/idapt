import { useUpload } from '../../chat/hooks/use-upload';
import { useGenerate } from '../hooks/use-generate';
import { compressData, arrayBufferToBase64 } from '../utils/compression';
import { useUploadContext } from '@/app/contexts/upload-context';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { upload, currentFile, isUploading, cancelUpload, currentConflict, resolveConflict } = useUpload();
  const { generate } = useGenerate();
  const { items } = useUploadContext();

  const uploadFile = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    const content = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsDataURL(file);
    });

    try {
      const filePath = folderId ? `${folderId}/${file.name}` : file.name;
      
      const compressed = compressData(content);
      const compressedBase64 = arrayBufferToBase64(compressed);
      
      await upload([{
        path: filePath,
        content: `data:${file.type};base64,${compressedBase64}`,
        name: file.name,
        file_created_at: file.lastModified / 1000,
        file_modified_at: file.lastModified / 1000,
      }], true);

      await generate([{
        path: filePath,
        transformations_stack_name_list: ["sentence-splitter-1024", "sentence-splitter-512", "sentence-splitter-128"]
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
    cancelUpload,
    currentConflict,
    resolveConflict,
    items
  };
} 