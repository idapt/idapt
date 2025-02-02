"use client";

import { File, Folder, MoreVertical, Download, Trash2, Info, Layers, X, CheckCircle2, Clock, AlertCircle, RefreshCcw, CircleDashed } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/app/components/ui/dialog";
import { Button } from "@/app/components/ui/button";
import { encodePathSafe } from "@/app/components/file-manager/utils/path-encoding";
import { useDeletionToast } from "@/app/components/file-manager/hooks/use-deletion-toast";
import { useApiClient } from '@/app/lib/api-client';
import { useUser } from "@/app/contexts/user-context";
import { useProcessingStacks } from '@/app/components/processing/hooks/use-processing-stacks';
import { useProcessing } from '@/app/components/file-manager/hooks/use-processing';
import {
  downloadFileRouteApiDatasourcesDatasourceNameFileManagerFileEncodedOriginalPathDownloadGet,
  downloadFolderRouteApiDatasourcesDatasourceNameFileManagerFolderEncodedOriginalPathDownloadGet,
  deleteRouteApiDatasourcesDatasourceNameFileManagerEncodedOriginalPathDelete,
  deleteProcessedDataRouteApiDatasourcesDatasourceNameFileManagerProcessedDataEncodedOriginalPathDelete
  // renameFileRouteApiFileManagerFilePathRenamePost,
  // renameFolderRouteApiFileManagerFolderPathRenamePost
} from '@/app/client';

interface FileItemProps {
  id: number;
  name: string;
  type: "file" | "folder";
  size?: string;
  modified: string;
  accessed: string;
  path: string;
  mimeType?: string;
  stacks_to_process?: string;
  processed_stacks?: string;
  error_message?: string;
  status?: string;
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
  stacks_to_process,
  processed_stacks,
  error_message,
  status,
  onClick, 
  onRefresh,
  viewMode = 'list'
}: FileItemProps) {
  const { stacks } = useProcessingStacks();
  const { processWithStack } = useProcessing();
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(name);
  const [showDetails, setShowDetails] = useState(false);
  const { startDeletion, completeDeletion, failDeletion } = useDeletionToast();
  const client = useApiClient();
  const { userId } = useUser();

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
    try {
      const encodedPath = encodePathSafe(path);
      
      // Use fetch directly to get the raw response // TODO: Use API client
      const url = type === 'folder' 
        ? `/api/datasources/file-manager/folder/${encodedPath}/download?user_id=${userId}`
        : `/api/datasources/file-manager/file/${encodedPath}/download?user_id=${userId}`;
      
      const response = await fetch(url);
  
      if (!response.ok) {
        throw new Error('Download failed');
      }
  
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = type === 'folder' ? name + '.zip' : name;
      
      try {
        document.body.appendChild(a);
        a.click();
      } finally {
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download item');
    }
  };
  

  const handleDelete = async () => {
    if (!path) return;
    
    if (confirm(`Are you sure you want to delete ${name}?`)) {
      try {
        const deletionId = startDeletion(name, path);
        const datasourceName = path.split('/')[0];
        if (!datasourceName) {
          throw new Error('Failed to get datasource name');
        }
        const encodedPath = encodePathSafe(path);
        const response = await deleteRouteApiDatasourcesDatasourceNameFileManagerEncodedOriginalPathDelete({
          client,
          path: { encoded_original_path: encodedPath, datasource_name: datasourceName },
          query: {
            user_id: userId
          }
        });
        if (!response.response.ok) {
          const error = await response.response.json();
          if (response.response.status === 409) {
              alert('This item is currently being processed and cannot be deleted. Please try again once processing is complete.');
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

  /*const handleRename = async () => {
    if (!path || newName === name) {
      setIsRenaming(false);
      return;
    }

    try {
      const encodedPath = encodePathSafe(path);
      const response = await renameFileRouteApiFileManagerFileEncodedOriginalPathRenamePost({
        client,
        body: {
          new_name: newName
        },
        path: { encoded_original_path: encodedPath }
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
  };*/

  const handleDeleteProcessedData = async () => {
    if (!path) return;
    
    if (confirm(`Are you sure you want to delete all processed data for ${name}?`)) {
      try {
        const datasourceName = path.split('/')[0];
        if (!datasourceName) {
          throw new Error('Failed to get datasource name');
        }
        const encodedPath = encodePathSafe(path);
        const response = await deleteProcessedDataRouteApiDatasourcesDatasourceNameFileManagerProcessedDataEncodedOriginalPathDelete({
          client,
          path: { encoded_original_path: encodedPath, datasource_name: datasourceName },
          query: {
            user_id: userId
          }
        });

        if (!response.response.ok) {
          throw new Error('Failed to delete processed data');
        }

        onRefresh?.();
      } catch (error) {
        console.error('Delete processed data failed:', error);
        alert(error instanceof Error ? error.message : 'Failed to delete processed data');
      }
    }
  };

  return (
    <>
      <div 
        className="group relative flex flex-col items-center w-full h-full hover:bg-gray-50 rounded-lg cursor-pointer"
        onClick={handleClick}
      >
        <div className="flex-1 flex items-center justify-center relative">
          {type === 'folder' ? (
            <Folder className="h-12 w-12 text-blue-500" />
          ) : (
            <File className="h-12 w-12 text-gray-500" />
          )}

          {status && (
            <div className="absolute bottom-2 -right-1 bg-white rounded-full">
              {status === "pending" && <CircleDashed className="h-5 w-5 text-red-500" />}
              {status === "queued" && <Clock className="h-5 w-5 text-yellow-500" />}
              {status === "completed" && <CheckCircle2 className="h-5 w-5 text-green-500" />}
              {status === "processing" && <RefreshCcw className="h-5 w-5 text-blue-500" />}
              {status === "error" && <AlertCircle className="h-5 w-5 text-red-500" />}
            </div>
          )}
        </div>

        <div className="w-full px-1 mt-2">
          <p className="text-sm font-medium text-gray-900 text-center truncate">{name}</p>
          {size && <p className="text-xs text-gray-500 text-center truncate">{size}</p>}
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-1 right-1 opacity-0 group-hover:opacity-100"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[200px] p-0.5 bg-white rounded-md shadow-md z-50">
            {stacks.map((stack) => (
              <DropdownMenuItem
                className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
                key={stack.identifier}
                onSelect={() => {
                  processWithStack([path], stack.identifier);
                }}
              >
                <Layers className="h-4 w-4 mr-2" />
                <span>Process with {stack.display_name}</span>
              </DropdownMenuItem>
            ))}
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
              onSelect={handleDeleteProcessedData}
            >
              <X className="h-4 w-4 mr-2" />
              <span>Delete Processed Data</span>
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
            
            {processed_stacks && (
              <div>
                <strong>Processed with stacks:</strong>
                <div className="mt-1">
                  {JSON.parse(processed_stacks).map((stack: string) => (
                    <span key={stack} className="inline-block bg-green-100 text-green-800 px-2 py-1 rounded mr-2 mb-2 text-sm">
                      {stack}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {stacks_to_process && (
              <div>
                <strong>Pending processing with stacks:</strong>
                <div className="mt-1">
                  {JSON.parse(stacks_to_process).map((stack: string) => (
                    <span key={stack} className="inline-block bg-yellow-100 text-yellow-800 px-2 py-1 rounded mr-2 mb-2 text-sm">
                      {stack}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {error_message && (
              <div className="mt-4">
                <strong className="text-red-600">Processing Error:</strong>
                <div className="mt-1 p-2 bg-red-50 text-red-700 rounded border border-red-200">
                  {error_message}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 