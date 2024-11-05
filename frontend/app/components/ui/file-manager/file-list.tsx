"use client";

import { FileItem } from "./file-item";

interface FileListProps {
  items: FileNode[];
  onFolderClick: (folder: FileNode) => void;
  onUploadComplete: () => void;
}

export function FileList({ items, onFolderClick, onUploadComplete }: FileListProps) {
  const filteredItems = items.filter(item => item.name !== '.');
  
  return (
    <div className="space-y-1 p-4">
      {filteredItems.map((item) => (
        <FileItem
          key={`${item.type}-${item.id}-${item.path}`}
          id={item.id}
          name={item.name}
          type={item.type as "file" | "folder"}
          size={item.size}
          modified={item.modified}
          path={item.path}
          onClick={() => item.type === 'folder' && onFolderClick(item)}
          onRefresh={onUploadComplete}
        />
      ))}
    </div>
  );
} 