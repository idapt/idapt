import { useUpload } from "../../chat/hooks/use-upload";
import { useUploadToast } from '@/app/hooks/use-upload-toast';

interface FolderUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFolderUpload() {
  const { upload, currentFile, isUploading, cancelUpload } = useUpload();
  const { startUpload, updateUpload, completeUpload, failUpload } = useUploadToast();

  const uploadFolder = async (folderInput: HTMLInputElement, targetPath: string = "", options?: FolderUploadOptions) => {
    if (!folderInput.files?.length) return;
    
    let toastIds: string[] = [];
    try {
      const files = Array.from(folderInput.files);
      
      // Create toast items for all files
      toastIds = files.map(file => 
        startUpload(
          file.name, 
          targetPath ? `${targetPath}/${file.webkitRelativePath}` : file.webkitRelativePath
        )
      );

      // Prepare upload items
      const uploadItems = await Promise.all(files.map(async (file, index) => {
        const content = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        });

        return {
          path: targetPath ? `${targetPath}/${file.webkitRelativePath}` : file.webkitRelativePath,
          content,
          name: file.name,
          file_created_at: file.lastModified / 1000,
          file_modified_at: file.lastModified / 1000,
        };
      }));

      // Upload files
        await upload(uploadItems,
        toastIds,
        (id, progress) => updateUpload(id, progress),
        (id) => completeUpload(id)
      );
      
      // Mark all uploads as complete
      toastIds.forEach(id => completeUpload(id));
      options?.onComplete?.();
    } catch (error) {
      // Mark all uploads as failed
      toastIds.forEach((id: string) => failUpload(id));
      options?.onError?.(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  return {
    uploadFolder,
    currentFile,
    isUploading,
    cancelUpload
  };
} 