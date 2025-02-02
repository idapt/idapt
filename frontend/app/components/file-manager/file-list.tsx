"use client";

import { FileItem } from "@/app/components/file-manager/file-item";
import { DatasourceItem } from "@/app/components/file-manager/datasource-item";

import { FileInfoResponse, FolderInfoResponse } from "@/app/client";
import { DatasourceResponse } from "@/app/client";

interface FileListProps {
  files: FileInfoResponse[];
  folders: FolderInfoResponse[];
  datasources?: DatasourceResponse[];
  viewMode: 'grid' | 'list';
  onFolderClick: (path: string) => void;
  onDatasourceClick?: (datasource: DatasourceResponse) => void;
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
    <div className={
      viewMode === 'grid' 
        ? "grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-2 p-4"
        : "space-y-1 p-4"
    }>
      {datasources?.map((datasource) => (
        <div key={`datasource-${datasource.identifier}`} className="w-[120px] h-[120px]">
          <DatasourceItem
            datasource={datasource}
            onClick={() => onDatasourceClick?.(datasource)}
            onRefresh={onUploadComplete}
          />
        </div>
      ))}
      {folders.map((folder) => (
        <div key={`folder-${folder.id}`} className="w-[120px] h-[120px]">
          <FileItem
            id={folder.id}
            name={folder.name}
            type="folder"
            path={folder.original_path}
            modified={folder.uploaded_at.toString()}
            accessed={folder.uploaded_at.toString()}
            onClick={() => onFolderClick(folder.original_path)}
            onRefresh={onUploadComplete}
            viewMode={viewMode}
          />
        </div>
      ))}
      {files.map((file) => (
        <div key={`file-${file.id}`} className="h-[120px] w-[120px]">
          <FileItem
            id={file.id}
            name={file.name}
            type="file"
            size={file.size?.toString()}
            modified={file.uploaded_at.toString()}
            accessed={file.uploaded_at.toString()}
            path={file.original_path}
            mimeType={file.mime_type ?? undefined}
            stacks_to_process={file.stacks_to_process ?? undefined}
            processed_stacks={file.processed_stacks ?? undefined}
            status={file.status}
            error_message={file.error_message ?? undefined}
            onRefresh={onUploadComplete}
            viewMode={viewMode}
          />
        </div>
      ))}
    </div>
  );
} 