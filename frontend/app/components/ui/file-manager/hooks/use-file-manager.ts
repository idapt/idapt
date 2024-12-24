import { File, Folder, Datasource } from '@/app/types/files';
import { useCallback, useEffect, useState } from 'react';
import { useClientConfig } from '../../chat/hooks/use-config';
import { encodePathSafe } from '@/app/components/ui/file-manager/utils/path-encoding';

export function useFileManager() {
  const { backend } = useClientConfig();
  const [currentPath, setCurrentPath] = useState<string>('');
  const [files, setFiles] = useState<File[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [datasources, setDatasources] = useState<Datasource[]>([]);
  const [currentDatasource, setCurrentDatasource] = useState<Datasource | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFolderContents = useCallback(async (path?: string) => {
    try {
      setLoading(true);
      const encodedPath = path ? encodePathSafe(path) : '';
      
      // Make requests in parallel using Promise.all
      const [folderResponse, datasourcesResponse] = await Promise.all([
        fetch(`${backend}/api/file-manager/folder/${encodedPath}`),
        fetch(`${backend}/api/datasources`)
      ]);

      if (!folderResponse.ok) throw new Error('Failed to fetch folder contents');
      if (!datasourcesResponse.ok) throw new Error('Failed to fetch datasources');

      const [folderData, datasources] = await Promise.all([
        folderResponse.json(),
        datasourcesResponse.json()
      ]);

      setFiles(folderData.files);
      setFolders(folderData.folders);
      setDatasources(datasources);

      // Set current datasource
      if (path) {
        const pathParts = path.split('/').filter(Boolean);
        if (pathParts.length > 0) {
          const datasourceIdentifier = pathParts[0];
          const currentDatasource = datasources.find(d => d.identifier === datasourceIdentifier);
          setCurrentDatasource(currentDatasource);
        }
      } else {
        setCurrentDatasource(undefined);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch folder contents');
    } finally {
      setLoading(false);
    }
  }, [backend]);

  const navigateToFolder = useCallback((path: string) => {
    setCurrentPath(path);
    fetchFolderContents(path);
  }, [fetchFolderContents]);

  // Initial load of root folder
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