"use client";

import { FileItem } from "./file-item";
import { File, Folder, Datasource } from "@/app/types/files";
import { DatasourceItem } from "./datasource-item";

interface FileListProps {
  files: File[];
  folders: Folder[];
  datasources?: Datasource[];
  viewMode: 'grid' | 'list';
  onFolderClick: (path: string) => void;
  onDatasourceClick?: (datasource: Datasource) => void;
  onUploadComplete: () => void;
}

export function FileList({ 
  files, 
  folders, 
  datasources,
  viewMode, 
  onFolderClick,
  onDatasourceClick,
  onUploadComplete 
}: FileListProps) {
  return (
    <div className={viewMode === 'grid' ? "grid grid-cols-4 gap-4 p-4" : "space-y-1 p-4"}>
      {datasources?.map((datasource) => (
        <DatasourceItem
          key={`datasource-${datasource.id}`}
          datasource={datasource}
          onClick={() => onDatasourceClick?.(datasource)}
          onRefresh={onUploadComplete}
        />
      ))}
      {folders.map((folder) => (
        <FileItem
          key={`folder-${folder.id}`}
          id={folder.id}
          name={folder.name}
          type="folder"
          path={folder.path}
          modified={folder.uploaded_at.toString()}
          accessed={folder.uploaded_at.toString()}
          onClick={() => onFolderClick(folder.path)}
          onRefresh={onUploadComplete}
          viewMode={viewMode}
        />
      ))}
      {files.map((file) => (
        <FileItem
          key={`file-${file.id}`}
          id={file.id}
          name={file.name}
          type="file"
          size={file.size}
          modified={file.uploaded_at.toString()}
          accessed={file.uploaded_at.toString()}
          path={file.path}
          mimeType={file.mime_type}
          onRefresh={onUploadComplete}
          viewMode={viewMode}
        />
      ))}
    </div>
  );
} 