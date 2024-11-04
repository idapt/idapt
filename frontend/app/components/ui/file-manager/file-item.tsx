"use client";

import { File, Folder, MoreVertical, Download, Trash2, Edit, Info } from "lucide-react";
import { Button } from "../button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";
import { useState } from "react";
import { useClientConfig } from "../chat/hooks/use-config";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../dialog";
import { Input } from "../input";

interface FileItemProps {
  id: number;
  name: string;
  type: "file" | "folder";
  size?: string;
  modified?: string;
  path?: string;
  onClick?: () => void;
  onRefresh?: () => void;
}

export function FileItem({ id, name, type, size, modified, path, onClick, onRefresh }: FileItemProps) {
  const { backend } = useClientConfig();
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(name);
  const [showDetails, setShowDetails] = useState(false);

  const handleDownload = async () => {
    try {
      const response = await fetch(`${backend}/api/file-manager/download/${id}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete ${name}?`)) {
      try {
        const response = await fetch(`${backend}/api/file-manager/${type}/${id}`, {
          method: 'DELETE',
        });
        if (response.ok) {
          onRefresh?.();
        }
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  const handleRename = async () => {
    try {
      const response = await fetch(`${backend}/api/file-manager/${type}/${id}/rename`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ newName }),
      });
      if (response.ok) {
        setIsRenaming(false);
        onRefresh?.();
      }
    } catch (error) {
      console.error('Rename failed:', error);
    }
  };

  return (
    <>
      <div 
        className="group relative flex items-center space-x-4 p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
        onClick={onClick}
      >
        {type === 'folder' ? (
          <Folder className="h-8 w-8 text-blue-500" />
        ) : (
          <File className="h-8 w-8 text-gray-500" />
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{name}</p>
          {size && <p className="text-sm text-gray-500">{size}</p>}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[200px] p-2">
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onClick={handleDownload}
            >
              <Download className="h-4 w-4 mr-2" />
              <span>Download</span>
            </DropdownMenuItem>
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onClick={() => setIsRenaming(true)}
            >
              <Edit className="h-4 w-4 mr-2" />
              <span>Rename</span>
            </DropdownMenuItem>
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onClick={() => setShowDetails(true)}
            >
              <Info className="h-4 w-4 mr-2" />
              <span>Details</span>
            </DropdownMenuItem>
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md text-red-600 flex items-center"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Rename Dialog */}
      <Dialog open={isRenaming} onOpenChange={setIsRenaming}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename {type}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 p-4">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter new name"
            />
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsRenaming(false)}>
                Cancel
              </Button>
              <Button onClick={handleRename}>
                Rename
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Details Dialog */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{name} Details</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 p-4">
            <p><strong>Type:</strong> {type}</p>
            {size && <p><strong>Size:</strong> {size}</p>}
            {modified && <p><strong>Modified:</strong> {modified}</p>}
            {path && <p><strong>Path:</strong> {path}</p>}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 