import { useState } from 'react';
import { useApiClient } from '@/app/lib/api-client';
import { FileUploadItem, uploadFileRouteApiDatasourcesDatasourceNameFileManagerUploadFilePost } from '@/app/client';

export function useFiles() {
  const client = useApiClient();
  const [isUploading, setIsUploading] = useState(false);

  const uploadFileApi = async (uploadItem: FileUploadItem) => {
    try {
      setIsUploading(true);
      // Extract datasource name from uploadItem.original_path
      const datasourceName = uploadItem.original_path.split('/')[0];
      await uploadFileRouteApiDatasourcesDatasourceNameFileManagerUploadFilePost({
        client,
        path: { datasource_name: datasourceName },
        body: uploadItem
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