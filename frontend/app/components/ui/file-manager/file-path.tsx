"use client";

import { ChevronRight, Home } from "lucide-react";
import { Button } from "../button";
import { File, Folder } from "@/app/types/files";

interface FilePathProps {
  currentPath: string;
  onNavigate: (folder_path: string) => void;
}

export function FilePath({ currentPath, onNavigate }: FilePathProps) {
  const pathParts = currentPath ? currentPath.split('/').filter(Boolean) : [];
  
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        className="flex items-center gap-1"
        onClick={() => onNavigate("")} // Navigate to root folder
      >
        <Home className="w-4 h-4" />
        <span>Home</span>
      </Button>
      
      {pathParts.length > 0 && pathParts.map((part, index) => {
        const pathUpToHere = pathParts.slice(0, index + 1).join('/');
        return (
          <div key={pathUpToHere} className="flex items-center">
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate(pathUpToHere)} // Navigate to folder
            >
              {part}
            </Button>
          </div>
        );
      })}
    </div>
  );
} 