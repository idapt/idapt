import { useUpload } from "../../chat/hooks/use-upload";
import { useGenerate } from "../hooks/use-generate";

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
      if (file.size > 0) {
        filePaths.push(fullPath);
      }

      // For files, we need to read their content
      if (file.size > 0) {
        const content = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        });

        uploadItems.push({
          path: fullPath,
          content,
          is_folder: false,
          name: file.name,
          mime_type: file.type,
          original_created_at: file.lastModified.toString(),
          original_modified_at: file.lastModified.toString()
        });
      } else {
        uploadItems.push({
          path: fullPath,
          content: "",
          is_folder: true,
          name: file.name,
          original_created_at: file.lastModified.toString(),
          original_modified_at: file.lastModified.toString()
        });
      }
    }

    try {
      await upload(uploadItems, true);
      
      // Generate index for uploaded files
      if (filePaths.length > 0) {
        await generate(filePaths);
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