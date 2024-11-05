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

    console.log('Files to upload:', files);

    for (const file of files) {
      const relativePath = file.webkitRelativePath;
      const fullPath = targetPath ? `${targetPath}/${relativePath}` : relativePath;
      
      console.log('Processing file:', {
        name: file.name,
        relativePath,
        fullPath
      });

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
        // For folders, we just need the path, name and metadata
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

    console.log('Final upload items:', uploadItems);

    try {
      await uploadToVault(uploadItems, true);
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