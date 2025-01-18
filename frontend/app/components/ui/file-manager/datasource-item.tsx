import { Database, MoreVertical, Settings, Trash2, Layers } from "lucide-react";
import { Button } from "../button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";
import { useState, useEffect } from "react";
import { useClientConfig } from "../chat/hooks/use-config";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../dialog";
import { Datasource } from "@/app/types/files";
import { encodePathSafe } from "./utils/path-encoding";
import { Textarea } from "../textarea";
import { useApiClient } from "@/app/lib/api-client";
import { useProcessingStacks } from "../processing/hooks/use-processing-stacks";
import useProcessing from "./hooks/use-processing";

interface DatasourceItemProps {
  datasource: Datasource;
  onClick?: () => void;
  onRefresh?: () => void;
}

export function DatasourceItem({ datasource, onClick, onRefresh }: DatasourceItemProps) {
  const { backend } = useClientConfig();
  const [showSettings, setShowSettings] = useState(false);
  const [description, setDescription] = useState(datasource.description || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { fetchWithAuth } = useApiClient();
  const { stacks } = useProcessingStacks();
  const { processFolder, processWithStack } = useProcessing();

  useEffect(() => {
    setDescription(datasource.description || '');
  }, [datasource.description]);

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

  const handleSaveSettings = async () => {
    try {
      setError(null);
      setIsSaving(true);
      const response = await fetchWithAuth(`${backend}/api/datasources/${encodePathSafe(datasource.identifier)}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      onRefresh?.();
      setShowSettings(false);
    } catch (error) {
      console.error('Save failed:', error);
      setError('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete datasource "${datasource.name}"?`)) {
        try {
            const encodedIdentifier = encodePathSafe(datasource.identifier);
            const response = await fetchWithAuth(`${backend}/api/datasources/${encodedIdentifier}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                if (response.status === 409) {
                    const detail = error.detail;
                    let message = `Some files could not be deleted:\n\n`;
                    
                    if (detail.processing_files.length > 0) {
                        message += `Files being processed:\n${detail.processing_files.join('\n')}\n\n`;
                    }
                    
                    if (detail.failed_files.length > 0) {
                        message += `Failed to delete:\n${detail.failed_files.join('\n')}\n\n`;
                    }
                    
                    if (detail.deleted_files.length > 0) {
                        message += `Successfully deleted:\n${detail.deleted_files.join('\n')}`;
                    }
                    
                    alert(message);
                    onRefresh?.();
                    return;
                }
                throw new Error(error.detail || 'Failed to delete datasource');
            }
            
            onRefresh?.();
        } catch (error) {
            console.error('Delete failed:', error);
            alert(error instanceof Error ? error.message : 'Failed to delete datasource');
        }
    }
  };

  return (
    <>
      <div 
        className="group relative flex items-center space-x-4 p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
        onClick={handleClick}
      >
        <Database className="h-8 w-8 text-gray-400" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{datasource.name}</p>
          <p className="text-xs text-gray-500">Datasource</p>
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
          {stacks.map((stack) => (
              <DropdownMenuItem
                className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
                key={stack.identifier}
                onSelect={() => {
                  processFolder(datasource.name, stack.identifier);
                }}
              >
                <Layers className="h-4 w-4 mr-2" />
                <span>Process with {stack.display_name}</span>
              </DropdownMenuItem>
            ))}
            <DropdownMenuItem 
              className="cursor-pointer p-2 hover:bg-gray-100 rounded-md flex items-center"
              onSelect={() => setShowSettings(true)}
            >
              <Settings className="h-4 w-4 mr-2" />
              <span>Settings</span>
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

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Datasource Settings</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 p-4">
            {error && (
              <div className="text-red-500 text-sm mb-2">{error}</div>
            )}
            <div>
              <label className="text-sm font-medium">Name</label>
              <p className="mt-1">{datasource.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium">Type</label>
              <p className="mt-1">{datasource.type}</p>
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Textarea
                className="mt-1"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter datasource description..."
                autoFocus={false}
              />
            </div>
            <div className="flex justify-end space-x-2 pt-4">
              <Button 
                variant="outline" 
                onClick={() => {
                  setDescription(datasource.description || '');
                  setShowSettings(false);
                }}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSaveSettings} 
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 