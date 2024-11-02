"use client";

import { Grid2X2, List, Upload, FolderUp } from "lucide-react";
import { useState } from "react";
import { Button } from "../button";
import { FileList } from "./file-list";
import { FileGrid } from "./file-grid";
import { FilePath } from "./file-path";

export function FileManager() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-sm p-4 space-y-4">
      <div className="flex justify-between items-center">
        <FilePath />
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4 mr-2" />
            Upload File
          </Button>
          <Button variant="outline" size="sm">
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
      {viewMode === "grid" ? <FileGrid /> : <FileList />}
    </div>
  );
}
