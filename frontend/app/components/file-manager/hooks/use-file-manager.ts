import {
   DatasourceResponse,
   FileInfoResponse,
   FolderInfoResponse,
   getDatasourceRouteApiDatasourcesDatasourceNameGet,
   getFolderInfoRouteApiDatasourcesDatasourceNameFileManagerFolderEncodedOriginalPathGet,
   getAllDatasourcesRouteApiDatasourcesGet
} from '@/app/client';
import { useCallback, useEffect, useState } from 'react';
import { useApiClient } from '@/app/lib/api-client';
import { encodePathSafe } from '../utils/path-encoding';

export function useFileManager() {
  const client = useApiClient();
  const [currentPath, setCurrentPath] = useState<string>('');
  const [files, setFiles] = useState<FileInfoResponse[]>([]);
  const [folders, setFolders] = useState<FolderInfoResponse[]>([]);
  const [datasources, setDatasources] = useState<DatasourceResponse[]>([]);
  const [currentDatasource, setCurrentDatasource] = useState<DatasourceResponse | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFolderContents = useCallback(async (path?: string) => {
    try {
      setLoading(true);
      
      const pathParts = path?.split('/').filter(Boolean);
      if ( !path || !pathParts || pathParts.length === 0) {
        // Only fetch datasources for root view
        const datasources = await getAllDatasourcesRouteApiDatasourcesGet({ client });
        setFiles([]);
        setFolders([]);
        setDatasources(datasources.data || []);
        setCurrentDatasource(undefined);
      } else {

        // Set current datasource
        const datasourceName = pathParts[0];
        const datasource = await getDatasourceRouteApiDatasourcesDatasourceNameGet(
          {
            client,
            path: { datasource_name: datasourceName },
          });
        setCurrentDatasource(datasource.data);
        
        // Fetch folder contents and datasources
        const encodedPath = encodePathSafe(path);
        const folderData = await getFolderInfoRouteApiDatasourcesDatasourceNameFileManagerFolderEncodedOriginalPathGet({
          client,
          path: { encoded_original_path: encodedPath, datasource_name: datasourceName },
          query: { include_child_folders_files_recursively: false }
        });

        setFiles(folderData.data?.child_files || []);
        setFolders(folderData.data?.child_folders || []);

      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch contents');
    } finally {
      setLoading(false);
    }
  }, [client]);

  const navigateToFolder = useCallback((path: string) => {
    setCurrentPath(path);
    fetchFolderContents(path);
  }, [fetchFolderContents]);

  // Initial load of datasources only
  useEffect(() => {
    fetchFolderContents();
  }, [fetchFolderContents]);

  return {
    files,
    folders,
    datasources,
    currentPath,
    currentDatasource,
    loading,
    error,
    navigateToFolder,
    refreshContents: () => fetchFolderContents(currentPath)
  };
} 