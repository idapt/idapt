"use client";

import { FileItem } from "./file-item";
import { FileNode } from "./types";

interface FileGridProps {
  items: FileNode[];
  viewMode: 'grid' | 'list';
  onFolderClick: (folder: FileNode) => void;
  onUploadComplete: () => void;
}

export function FileGrid({ items, viewMode, onFolderClick, onUploadComplete }: FileGridProps) {
  const filteredItems = items.filter(item => item.name !== '.');
  
  return (
    <div className={viewMode === 'grid' ? "grid grid-cols-4 gap-4 p-4" : "space-y-1 p-4"}>
      {filteredItems.map((item) => (
        <FileItem
          key={item.id}
          id={item.id}
          name={item.name}
          type={item.type as "file" | "folder"}
          size={item.size}
          modified={item.modified}
          path={item.path}
          onClick={() => item.type === 'folder' && onFolderClick(item)}
          onRefresh={onUploadComplete}
          viewMode={viewMode}
        />
      ))}
    </div>
  );
} 