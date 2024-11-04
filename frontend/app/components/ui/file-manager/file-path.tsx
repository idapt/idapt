"use client";

import { ChevronRight, Home } from "lucide-react";
import { Button } from "../button";
import { FileNode } from "./types";

interface FilePathProps {
  folder: FileNode | null;
  path: FileNode[];
  onNavigate: (folder: FileNode | null) => void;
}

export function FilePath({ folder, path = [], onNavigate }: FilePathProps) {
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        className="flex items-center gap-1"
        onClick={() => onNavigate(null)}
      >
        <Home className="w-4 h-4" />
        <span>Home</span>
      </Button>
      
      {path.length > 0 && path.map((item, index) => (
        <div key={item.id} className="flex items-center">
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onNavigate(item)}
          >
            {item.name}
          </Button>
        </div>
      ))}
    </div>
  );
} 