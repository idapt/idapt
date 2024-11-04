import { useVaultUpload } from "../../chat/hooks/use-vault-upload";

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { uploadToVault, progress, currentConflict, resolveConflict } = useVaultUpload();

  const uploadFile = async (file: File, targetPath: string = "", options?: FileUploadOptions) => {
    const content = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsDataURL(file);
    });

    const fullPath = targetPath ? `${targetPath}/${file.name}` : file.name;

    try {
      await uploadToVault([{
        path: fullPath,
        content,
        is_folder: false,
        name: file.name
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