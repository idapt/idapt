import { useUpload } from "../../chat/hooks/use-upload";
import { useGenerate, GenerateFile } from "../hooks/use-generate";
import { compressData, arrayBufferToBase64 } from "../utils/compression";

interface FolderUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFolderUpload() {
  const { upload, progress } = useUpload();
  const { generate } = useGenerate();

  const uploadFolder = async (folderInput: HTMLInputElement, targetPath: string = "", options?: FolderUploadOptions) => {
    if (!folderInput.files || folderInput.files.length === 0) return;

    const files = Array.from(folderInput.files);
    const uploadItems = [];
    const filePaths = [];

    console.log('Files to upload:', files);

    for (const file of files) {
      const relativePath = file.webkitRelativePath;
      const fullPath = targetPath ? `${targetPath}/${relativePath}` : relativePath;

      // Store file paths for generation
      filePaths.push(fullPath);

      const content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      // Compress the file content
      const compressed = compressData(content);
      const compressedBase64 = arrayBufferToBase64(compressed);

      uploadItems.push({
        path: fullPath,
        content: `data:${file.type};base64,${compressedBase64}`,
        name: file.name,
        mime_type: file.type,
        original_created_at: file.lastModified.toString(),
        original_modified_at: file.lastModified.toString(),
        //compressed: true // Add flag to indicate compression
      });
    }

    try {
      await upload(uploadItems, true);
      
      // Generate index for uploaded files
      if (filePaths.length > 0) {
        // List of GenerateFile objects
        const generateFiles: GenerateFile[] = filePaths.map(filePath => ({
          path: filePath,
          transformations_stack_name_list: ["hierarchical"]  // Can be extended to support multiple transformations
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
    progress
  };
} 