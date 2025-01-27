import { File, Folder } from '@/app/types/files';
import { DatasourceResponse } from '@/app/types/datasources';
import { useCallback, useEffect, useState } from 'react';
import { useClientConfig } from '../../chat/hooks/use-config';
import { encodePathSafe } from '@/app/components/file-manager/utils/path-encoding';
import { useApiClient } from '@/app/lib/api-client';

export function useFileManager() {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();
  const [currentPath, setCurrentPath] = useState<string>('');
  const [files, setFiles] = useState<File[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [datasources, setDatasources] = useState<DatasourceResponse[]>([]);
  const [currentDatasource, setCurrentDatasource] = useState<DatasourceResponse | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFolderContents = useCallback(async (path?: string) => {
    try {
      setLoading(true);
      
      if (!path) {
        // Only fetch datasources for root view
        const datasourcesResponse = await fetchWithAuth(`${backend}/api/datasources`);
        if (!datasourcesResponse.ok) throw new Error('Failed to fetch datasources');
        const datasources = await datasourcesResponse.json();
        setFiles([]);
        setFolders([]);
        setDatasources(datasources);
        setCurrentDatasource(undefined);
      } else {
        // Fetch folder contents and datasources
        const encodedPath = encodePathSafe(path);
        const [folderResponse, datasourcesResponse] = await Promise.all([
          fetchWithAuth(`${backend}/api/file-manager/folder/${encodedPath}?include_child_folders_files_recursively=false`),
          fetchWithAuth(`${backend}/api/datasources`)
        ]);

        if (!folderResponse.ok) throw new Error('Failed to fetch folder contents');
        if (!datasourcesResponse.ok) throw new Error('Failed to fetch datasources');

        const [folderData, datasources] = await Promise.all([
          folderResponse.json(),
          datasourcesResponse.json()
        ]);

        setFiles(folderData.child_files);
        setFolders(folderData.child_folders);
        setDatasources(datasources);

        // Set current datasource
        const pathParts = path.split('/').filter(Boolean);
        if (pathParts.length > 0) {
          const datasourceIdentifier = pathParts[0];
          const currentDatasource = datasources.find((d: DatasourceResponse) => d.identifier === datasourceIdentifier);
          setCurrentDatasource(currentDatasource);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch contents');
    } finally {
      setLoading(false);
    }
  }, [backend, fetchWithAuth]);

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