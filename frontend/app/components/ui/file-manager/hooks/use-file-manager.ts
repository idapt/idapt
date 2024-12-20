import { FolderContentsResponse, File, Folder, Datasource } from '@/app/types/files';
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
      const url = `${backend}/api/file-manager/folder/${encodedPath}`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch folder contents');
      const data: FolderContentsResponse = await response.json();
      
      setFiles(data.files);
      setFolders(data.folders);
      
      // Get the datasources
      const datasourcesResponse = await fetch(`${backend}/api/datasources`);
      const datasources: Datasource[] = await datasourcesResponse.json();
      setDatasources(datasources);
      setCurrentDatasource(data.datasource);
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