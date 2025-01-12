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
import { encodePathSafe } from "@/app/components/ui/file-manager/utils/path-encoding";
import { useDeletionToast } from "@/app/components/ui/file-manager/hooks/use-deletion-toast";
import { useApiClient } from "@/app/lib/api-client";

interface FileItemProps {
  id: number;
  name: string;
  type: "file" | "folder";
  size?: string;
  modified: string;
  accessed: string;
  path: string;
  mimeType?: string;
  onClick?: () => void;
  onRefresh?: () => void;
  viewMode?: 'grid' | 'list';
}

export function FileItem({ 
  id, 
  name, 
  type, 
  size, 
  modified, 
  accessed,
  path,
  mimeType,
  onClick, 
  onRefresh,
  viewMode = 'list'
}: FileItemProps) {
  const { backend } = useClientConfig();
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(name);
  const [showDetails, setShowDetails] = useState(false);
  const { startDeletion, completeDeletion, failDeletion } = useDeletionToast();
  const { fetchWithAuth } = useApiClient();

  const handleClick = (e: React.MouseEvent) => {
    // Check if the click came from the dropdown menu or its children
    if (e.target instanceof Element && (
      e.target.closest('[role="menu"]') || 
      e.target.closest('button[role="trigger"]')
    )) {
      e.stopPropagation();
      return;
    }
    onClick?.();
  };

  const handleDownload = async () => {
    const encodedPath = encodePathSafe(path);
    const response = await fetchWithAuth(`${backend}/api/file-manager/${type}/${encodedPath}/download`, {
      method: 'GET',
    });
    
    // Download the file or folder zip with the right file or folder name
    if (!response.ok) {
      throw new Error('Download failed');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    // Use original name with .zip extension for folders
    a.download = type === 'folder' ? `${name}.zip` : name;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleDelete = async () => {
    if (!path) return;
    
    if (confirm(`Are you sure you want to delete ${name}?`)) {
      try {
        const deletionId = startDeletion(name, path);
        const encodedPath = encodePathSafe(path);
        const response = await fetchWithAuth(`${backend}/api/file-manager/${type}/${encodedPath}`, {
          method: 'DELETE'
        });

        if (!response.ok) {
          const error = await response.json();
          if (response.status === 409) {
            alert('This file is currently being processed and cannot be deleted. Please try again once processing is complete.');
            failDeletion(deletionId);
            return;
          }
          throw new Error(error.detail || 'Delete failed');
        }

        completeDeletion(deletionId);
        onRefresh?.();
      } catch (error) {
        console.error('Delete failed:', error);
        alert(error instanceof Error ? error.message : 'Failed to delete item');
      }
    }
  };

  const handleRename = async () => {
    if (!path || newName === name) {
      setIsRenaming(false);
      return;
    }

    try {
      const encodedPath = encodePathSafe(path);
      const response = await fetchWithAuth(`${backend}/api/file-manager/${type}/${encodedPath}/rename`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_name: newName
        }),
      });

      if (response.ok) {
        onRefresh?.();
        setIsRenaming(false);
      } else {
        throw new Error('Rename failed');
      }
    } catch (error) {
      console.error('Rename failed:', error);
      alert('Failed to rename item');
    }
  };

  return (
    <>
      <div 
        className="group relative flex items-center space-x-4 p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
        onClick={handleClick}
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
          <DropdownMenuContent align="end" className="w-[200px] p-0.5 bg-white rounded-md shadow-md z-50">
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onSelect={handleDownload}
            >
              <Download className="h-4 w-4 mr-2" />
              <span>Download</span>
            </DropdownMenuItem>
            {/* <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onSelect={() => setIsRenaming(true)}
            >
              <Edit className="h-4 w-4 mr-2" />
              <span>Rename</span>
            </DropdownMenuItem> */}
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onSelect={() => setShowDetails(true)}
            >
              <Info className="h-4 w-4 mr-2" />
              <span>Details</span>
            </DropdownMenuItem>
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md text-red-600 flex items-center"
              onSelect={handleDelete}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Rename Dialog */}
      {/* <Dialog open={isRenaming} onOpenChange={setIsRenaming}> // Not working for now // TODO
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
      </Dialog> */}

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
            {accessed && <p><strong>Last Accessed:</strong> {accessed}</p>}
            {path && <p><strong>Path:</strong> {path}</p>}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 