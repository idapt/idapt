"use client";

import { Grid2X2, List, Upload, FolderUp, Loader2 } from "lucide-react";
import { useRef, useState, useCallback, useEffect } from "react";
import { Button } from "../button";
import { FileList } from "./file-list";
import { FileGrid } from "./file-grid";
import { FilePath } from "./file-path";
import { useFileUpload } from "./hooks/use-file-upload";
import { useFolderUpload } from "./hooks/use-folder-upload";
import { useFileManager } from './hooks/use-file-manager';
import { useClientConfig } from '../../chat/hooks/use-config';
import { FileNode } from '../types';

export function FileManager() {
  const {
    contents,
    currentFolder,
    loading,
    error,
    navigateToFolder,
    refreshContents
  } = useFileManager();
  
  const { uploadFile } = useFileUpload();
  const { uploadFolder } = useFolderUpload();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [path, setPath] = useState<FileNode[]>([]);

  const handleUploadComplete = () => {
    refreshContents();
  };

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-4 border-b">
        <FilePath folder={currentFolder} onNavigate={navigateToFolder} />
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <Grid2X2 className={viewMode === 'grid' ? 'text-primary' : ''} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setViewMode('list')}
          >
            <List className={viewMode === 'list' ? 'text-primary' : ''} />
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center flex-1">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : (
        <FileGrid
          items={contents}
          viewMode={viewMode}
          onFolderClick={navigateToFolder}
          onUploadComplete={handleUploadComplete}
        />
      )}
    </div>
  );
}
