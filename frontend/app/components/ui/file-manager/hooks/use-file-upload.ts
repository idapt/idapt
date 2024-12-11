import { useUpload } from '../../chat/hooks/use-upload';
import { useGenerate } from '../hooks/use-generate';
import { compressData, arrayBufferToBase64 } from '../utils/compression';

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
      
      // Compress the file content
      const compressed = compressData(content);
      const compressedBase64 = arrayBufferToBase64(compressed);
      
      await upload([{
        path: filePath,
        content: `data:${file.type};base64,${compressedBase64}`,
        name: file.name,
        mime_type: file.type,
        original_created_at: file.lastModified.toString(),
        original_modified_at: file.lastModified.toString(),
        //compressed: true // Add flag to indicate compression
      }], true);

      await generate([{
        path: filePath,
        transformations_stack_name_list: ["hierarchical"] // Can be extended to support multiple transformations
      }]);
      
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