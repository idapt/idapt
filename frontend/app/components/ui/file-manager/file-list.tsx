"use client";

import { FileItem } from "./file-item";

interface FileListProps {
  items: FileNode[];
  onFolderClick: (folder: FileNode) => void;
  onUploadComplete: () => void;
}

export function FileList({ items, onFolderClick }: FileListProps) {
  const filteredItems = items.filter(item => item.name !== '.');
  
  return (
    <div className="space-y-1 p-4">
      {filteredItems.map((item) => (
        <FileItem
          key={item.id}
          name={item.name}
          type={item.type as "file" | "folder"}
          onClick={() => item.type === 'folder' && onFolderClick(item)}
        />
      ))}
    </div>
  );
} 