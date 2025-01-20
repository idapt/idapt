import { useFiles } from "@/app/components/file-manager/hooks/use-upload";
import { useUploadToast } from "@/app/components/toasts/hooks/use-upload-toast";

interface FolderUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
  batchSize?: number;
}

export function useFolderUpload() {
  const { uploadFileApi, isUploading } = useFiles();
  const { startUpload, updateUpload, completeUpload, failUpload } = useUploadToast();

  const processFileInBatch = async (
    file: File,
    targetPath: string,
    toastId: string
  ): Promise<void> => {
    try {
      // Convert file to base64 with proper memory handling
      const base64Content = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const content = reader.result as string;
          const mimeType = file.type || 'application/octet-stream';
          resolve(`data:${mimeType};base64,${content.split(',')[1]}`);
          reader.onerror = () => reject(reader.error);
        };
        reader.readAsDataURL(file);
      });

      await uploadFileApi({
        original_path: targetPath ? `${targetPath}/${file.webkitRelativePath}` : file.webkitRelativePath,
        base64_content: base64Content,
        name: file.name,
        file_created_at: file.lastModified / 1000,
        file_modified_at: file.lastModified / 1000,
      });

      completeUpload(toastId);
    } catch (error) {
      failUpload(toastId);
      throw error;
    }
  };

  const uploadFolder = async (
    folderInput: HTMLInputElement, 
    targetPath: string = "", 
    options?: FolderUploadOptions
  ) => {
    if (!folderInput.files?.length) return;

    const files = Array.from(folderInput.files);
    const batchSize = options?.batchSize || 3; // Process 3 files at a time by default
    let toastIds: string[] = [];

    try {
      // Create toast items for all files first
      toastIds = files.map(file => 
        startUpload(
          file.name, 
          targetPath ? `${targetPath}/${file.webkitRelativePath}` : file.webkitRelativePath
        )
      );

      // Process files in batches
      for (let i = 0; i < files.length; i += batchSize) {
        const batch = files.slice(i, i + batchSize);
        
        // Process batch concurrently
        await Promise.all(
          batch.map((file, index) => 
            processFileInBatch(
              file,
              targetPath,
              toastIds[i + index]
            )
          )
        );

        // Calculate and report progress
        const progress = Math.min(((i + batchSize) / files.length) * 100, 100);
        options?.onProgress?.(progress);
      }

      options?.onComplete?.();
    } catch (error) {
      // Mark remaining uploads as failed
      toastIds.forEach(id => failUpload(id));
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFolder,
    isUploading
  };
} 