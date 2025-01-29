import { DatasourceResponse, FileInfoResponse, FolderInfoResponse } from '@/app/client';
import { useCallback, useEffect, useState } from 'react';
import { useApiClient } from '@/app/lib/api-client';
import {
  getDatasourcesRouteApiDatasourcesGet,
  getFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGet
} from '@/app/client';
import { useUser } from '@/app/contexts/user-context';
import { encodePathSafe } from '../utils/path-encoding';

export function useFileManager() {
  const client = useApiClient();
  const { userId } = useUser();
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
      
      if (!path) {
        // Only fetch datasources for root view
        const datasources = await getDatasourcesRouteApiDatasourcesGet({ client, query: { user_id: userId } });
        setFiles([]);
        setFolders([]);
        setDatasources(datasources.data || []);
        setCurrentDatasource(undefined);
      } else {
        // Fetch folder contents and datasources
        const encodedPath = encodePathSafe(path);
        const [folderData, datasources] = await Promise.all([
          getFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGet({
            client,
            path: { encoded_original_path: encodedPath },
            query: { include_child_folders_files_recursively: false, user_id: userId }
          }),
          getDatasourcesRouteApiDatasourcesGet({ client, query: { user_id: userId } })
        ]);

        setFiles(folderData.data?.child_files || []);
        setFolders(folderData.data?.child_folders || []);
        setDatasources(datasources.data || []);

        // Set current datasource
        const pathParts = path.split('/').filter(Boolean);
        if (pathParts.length > 0) {
          const datasourceIdentifier = pathParts[0];
          const currentDatasource = datasources.data?.find(d => d.identifier === datasourceIdentifier);
          setCurrentDatasource(currentDatasource);
        }
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