"use client";

import { Grid2X2, List, Upload, FolderUp, Plus, Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/app/components/ui/button";
import { FileList } from "@/app/components/file-manager/file-list";
import { FilePath } from "@/app/components/file-manager/file-path";
import { useFileUpload } from "@/app/components/file-manager/hooks/use-file-upload";
import { useFolderUpload } from "@/app/components/file-manager/hooks/use-folder-upload";
import { useFileManager } from "@/app/components/file-manager/hooks/use-file-manager";
import { DatasourceResponse } from "@/app/types/datasources";
import { CreateDatasourceDialog } from "@/app/components/file-manager/create-datasource-dialog";

export function FileManager() {
  const {
    currentPath,
    currentDatasource,
    files,
    folders,
    datasources,
    error,
    loading,
    navigateToFolder,
    refreshContents
  } = useFileManager();

  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [showCreateDatasource, setShowCreateDatasource] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const { uploadFile } = useFileUpload();
  const { uploadFolder } = useFolderUpload();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadFile(file, currentPath, {
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
      await uploadFolder(e.target, currentPath, {
        onError: (error) => alert(error),
        onComplete: () => {
          if (folderInputRef.current) folderInputRef.current.value = '';
          refreshContents();
        }
      });
    }
  };

  const handleDatasourceClick = (datasource: DatasourceResponse) => {
    navigateToFolder(`${datasource.name}`); // The name is used as the original path equivalent
  };

  const displayItems = currentPath === '' ? {
    files: [],
    folders: [],
    datasources: datasources
  } : {
    files,
    folders,
    datasources: undefined
  };

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-sm p-4 space-y-4">
      <div className="flex justify-between items-center">
        <FilePath 
          currentPath={currentPath} 
          currentDatasource={currentDatasource}
          onNavigate={navigateToFolder} 
        />
        <div className="flex space-x-2">
          {currentPath === '' ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCreateDatasource(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              New Datasource
            </Button>
          ) : (
            <>
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
                // @ts-expect-error
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
            </>
          )}
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
        <FileList 
          files={displayItems.files}
          folders={displayItems.folders}
          datasources={displayItems.datasources}
          viewMode={viewMode}
          onFolderClick={navigateToFolder}
          onDatasourceClick={handleDatasourceClick}
          onUploadComplete={refreshContents}
        />
      )}
      <CreateDatasourceDialog 
        open={showCreateDatasource}
        onClose={() => setShowCreateDatasource(false)}
        onCreated={refreshContents}
      />
    </div>
  );
}
