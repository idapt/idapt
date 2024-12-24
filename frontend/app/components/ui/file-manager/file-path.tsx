"use client";

import { ChevronRight, Home, Database } from "lucide-react";
import { Button } from "../button";
import { Datasource } from "@/app/types/files";

interface FilePathProps {
  currentPath: string;
  currentDatasource?: Datasource;
  onNavigate: (folder_path: string) => void;
}

export function FilePath({ currentPath, currentDatasource, onNavigate }: FilePathProps) {
  const pathParts = currentPath ? currentPath.split('/').filter(Boolean) : [];
  
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        className="flex items-center gap-1"
        onClick={() => onNavigate("")}
      >
        <Home className="w-4 h-4" />
        <span>Datasources</span>
      </Button>
      
      {pathParts.length > 0 && pathParts.map((part, index) => {
        // Rebuild the path up to here for the navigation
        const pathUpToHere = pathParts.slice(0, index + 1).join('/');
        // If this is a datasource, display using database object
        if (index === 0 && part == currentDatasource?.identifier) {
          return (
            <div key={pathUpToHere} className="flex items-center gap-1">
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center gap-1"
                onClick={() => onNavigate(pathUpToHere)}
              >
                <Database className="w-4 h-4" />
                <span>{currentDatasource.name}</span>
              </Button>
            </div>
          );
        }
        else {
          return (
            <div key={pathUpToHere} className="flex items-center gap-1">
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center gap-1"
                onClick={() => onNavigate(pathUpToHere)}
              >
                {part}
              </Button>
            </div>
          );
        }
      })}
    </div>
  );
} 