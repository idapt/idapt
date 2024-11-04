import { useCallback, useEffect, useState } from 'react';
import { useClientConfig } from '../../chat/hooks/use-config';
import { FileNode } from '../types';

export function useFileManager() {
  const { backend } = useClientConfig();
  const [currentFolder, setCurrentFolder] = useState<FileNode | null>(null);
  const [path, setPath] = useState<FileNode[]>([]);
  const [contents, setContents] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFolderContents = useCallback(async (folderId?: number) => {
    try {
      setLoading(true);
      const url = folderId !== undefined 
        ? `${backend}/api/file-manager/folder/${folderId}`
        : `${backend}/api/file-manager/folder`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch folder contents');
      const data = await response.json();
      setContents(data.filter(item => item.name !== '.'));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch folder contents');
    } finally {
      setLoading(false);
    }
  }, [backend]);

  const navigateToFolder = useCallback((folder: FileNode | null) => {
    setCurrentFolder(folder);
    if (!folder) {
      // Navigate to root
      setPath([]);
    } else if (path.find(p => p.id === folder.id)) {
      // Navigate to existing path item
      setPath(path.slice(0, path.findIndex(p => p.id === folder.id) + 1));
    } else {
      // Navigate to new folder
      setPath([...path, folder]);
    }
    fetchFolderContents(folder?.id);
  }, [path, fetchFolderContents]);

  // Initial load of root folder
  useEffect(() => {
    fetchFolderContents();
  }, [fetchFolderContents]);

  return {
    contents,
    currentFolder,
    path,
    loading,
    error,
    navigateToFolder,
    refreshContents: () => fetchFolderContents(currentFolder?.id)
  };
} 