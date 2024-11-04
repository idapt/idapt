"use client";

import { Grid2X2, List, Upload, FolderUp, Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "../button";
import { FileList } from "./file-list";
import { FileGrid } from "./file-grid";
import { FilePath } from "./file-path";
import { useFileUpload } from "./hooks/use-file-upload";
import { useFolderUpload } from "./hooks/use-folder-upload";
import { useFileManager } from './hooks/use-file-manager';

export function FileManager() {
  const {
    contents,
    currentFolder,
    path,
    loading,
    error,
    navigateToFolder,
    refreshContents
  } = useFileManager();
  
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const { uploadFile } = useFileUpload();
  const { uploadFolder } = useFolderUpload();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const folderPath = path.map(p => p.name).join('/');
      await uploadFile(file, folderPath, {
        onError: (error) => alert(error),
        onComplete: () => {
          if (fileInputRef.current) fileInputRef.current.value = '';
          refreshContents();
        }
      });
    }
  };

  const handleFolderUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const folderPath = path.map(p => p.name).join('/');
      await uploadFolder(e.target, folderPath, {
        onError: (error) => alert(error),
        onComplete: () => {
          if (folderInputRef.current) folderInputRef.current.value = '';
          refreshContents();
        }
      });
    }
  };

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-sm p-4 space-y-4">
      <div className="flex justify-between items-center">
        <FilePath folder={currentFolder} path={path} onNavigate={navigateToFolder} />
        <div className="flex space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileUpload}
          />
          <input
            type="file"
            ref={folderInputRef}
            className="hidden"
            webkitdirectory=""
            directory=""
            onChange={handleFolderUpload}
          />
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload File
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => folderInputRef.current?.click()}
          >
            <FolderUp className="h-4 w-4 mr-2" />
            Upload Folder
          </Button>
          <div className="border-l h-6 mx-2" />
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("grid")}
          >
            <Grid2X2 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>
      {loading ? (
        <div className="flex items-center justify-center flex-1">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : (
        viewMode === "grid" ? 
          <FileGrid 
            items={contents} 
            viewMode={viewMode} 
            onFolderClick={navigateToFolder} 
            onUploadComplete={refreshContents} 
          /> : 
          <FileList 
            items={contents} 
            onFolderClick={navigateToFolder} 
            onUploadComplete={refreshContents} 
          />
      )}
    </div>
  );
}
