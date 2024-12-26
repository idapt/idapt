import { useUpload } from "../../chat/hooks/use-upload";
import { useGenerate, GenerateFile } from "../hooks/use-generate";
import { compressData, arrayBufferToBase64 } from "../utils/compression";
import { useUploadContext } from '@/app/contexts/upload-context';

interface FolderUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFolderUpload() {
  const { upload, currentFile, isUploading, cancelUpload } = useUpload();
  const { generate } = useGenerate();
  const { items } = useUploadContext();

  const uploadFolder = async (folderInput: HTMLInputElement, targetPath: string = "", options?: FolderUploadOptions) => {
    if (!folderInput.files || folderInput.files.length === 0) return;

    const files = Array.from(folderInput.files);
    const uploadItems = [];
    const filePaths = [];

    for (const file of files) {
      const relativePath = file.webkitRelativePath;
      const fullPath = targetPath ? `${targetPath}/${relativePath}` : relativePath;

      filePaths.push(fullPath);

      const content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      const compressed = compressData(content);
      const compressedBase64 = arrayBufferToBase64(compressed);

      uploadItems.push({
        path: fullPath,
        content: `data:${file.type};base64,${compressedBase64}`,
        name: file.name,
        file_created_at: file.lastModified / 1000,
        file_modified_at: file.lastModified / 1000,
      });
    }

    try {
      await upload(uploadItems, true);
      
      if (filePaths.length > 0) {
        const generateFiles: GenerateFile[] = filePaths.map(filePath => ({
          path: filePath,
          transformations_stack_name_list: ["sentence-splitter-1024", "sentence-splitter-512", "sentence-splitter-128"]
        }));

        await generate(generateFiles);
      }
      
      options?.onComplete?.();
    } catch (error) {
      console.error('Upload error:', error);
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFolder,
    currentFile,
    isUploading,
    cancelUpload,
    items
  };
} 