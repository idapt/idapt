"use client";

import { FileItem } from "./file-item";
import { FileNode } from "./types";

interface FileGridProps {
  items: FileNode[];
  viewMode: 'grid' | 'list';
  onFolderClick: (folder: FileNode) => void;
  onUploadComplete: () => void;
}

export function FileGrid({ items, viewMode, onFolderClick }: FileGridProps) {
  return (
    <div className={viewMode === 'grid' ? "grid grid-cols-4 gap-4 p-4" : "space-y-1 p-4"}>
      {items.map((item) => (
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