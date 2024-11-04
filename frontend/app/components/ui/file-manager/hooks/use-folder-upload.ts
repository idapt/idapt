import { useVaultUpload } from "../../chat/hooks/use-vault-upload";

interface FolderUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFolderUpload() {
  const { uploadToVault, progress } = useVaultUpload();

  const uploadFolder = async (folderInput: HTMLInputElement, targetPath: string = "", options?: FolderUploadOptions) => {
    if (!folderInput.files || folderInput.files.length === 0) return;

    const files = Array.from(folderInput.files);
    const uploadItems = [];

    for (const file of files) {
      // Get the relative path of the file within the selected folder
      const relativePath = file.webkitRelativePath;
      const fullPath = targetPath ? `${targetPath}/${relativePath}` : relativePath;
      
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
          name: file.name
        });
      } else {
        // For folders, we just need the path
        uploadItems.push({
          path: fullPath,
          content: "",
          is_folder: true,
          name: file.name
        });
      }
    }

    try {
      await uploadToVault(uploadItems, true);
      options?.onComplete?.();
    } catch (error) {
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFolder,
    progress
  };
} 