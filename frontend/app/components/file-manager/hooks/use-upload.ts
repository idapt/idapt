import { useState } from 'react';
import { useApiClient } from '@/app/lib/api-client';
import { FileUploadItem, uploadFileRouteApiDatasourcesFileManagerUploadFilePost } from '@/app/client';
import { useUser } from '@/app/contexts/user-context';

export function useFiles() {
  const client = useApiClient();
  const { userId } = useUser();
  const [isUploading, setIsUploading] = useState(false);

  const uploadFileApi = async (uploadItem: FileUploadItem) => {
    try {
      setIsUploading(true);
      
      await uploadFileRouteApiDatasourcesFileManagerUploadFilePost({
        client,
        body: uploadItem,
        query: { user_id: userId }
      });
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  return {
    uploadFileApi,
    isUploading
  };
}