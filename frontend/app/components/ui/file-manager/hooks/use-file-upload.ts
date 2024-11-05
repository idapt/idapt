import { useUpload } from '../../chat/hooks/use-upload';

interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useFileUpload() {
  const { upload, progress, currentConflict, resolveConflict } = useUpload();

  const uploadFile = async (file: File, folderId: string = "", options?: FileUploadOptions) => {
    const content = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsDataURL(file);
    });

    try {
      await upload([{
        path: folderId ? `${folderId}/${file.name}` : file.name,
        content,
        is_folder: false,
        name: file.name,
        mime_type: file.type,
        original_created_at: file.lastModified.toString(),
        original_modified_at: file.lastModified.toString()
      }], true);
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