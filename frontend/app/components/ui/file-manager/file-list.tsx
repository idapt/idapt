"use client";

import { FileItem } from "./file-item";
import { File, Folder } from "@/app/types/files";

interface FileListProps {
  files: File[];
  folders: Folder[];
  viewMode: 'grid' | 'list';
  onFolderClick: (path: string) => void;
  onUploadComplete: () => void;
}

export function FileList({ files, folders, viewMode, onFolderClick, onUploadComplete }: FileListProps) {
  return (
    <div className={viewMode === 'grid' ? "grid grid-cols-4 gap-4 p-4" : "space-y-1 p-4"}>
      {folders.map((folder) => (
        <FileItem
          key={`folder-${folder.id}`}
          id={folder.id}
          name={folder.name}
          type="folder"
          path={folder.path}
          modified={folder.uploaded_at}
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
          modified={file.uploaded_at}
          path={file.path}
          mimeType={file.mime_type}
          onRefresh={onUploadComplete}
          viewMode={viewMode}
        />
      ))}
    </div>
  );
} 