import { Database, MoreVertical, Settings, Trash2, Layers } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/app/components/ui/dialog";
import { DatasourceResponse } from "@/app/types/datasources";
import { Textarea } from "@/app/components/ui/textarea";
import { useProcessingStacks } from "@/app/components/processing/hooks/use-processing-stacks";
import useProcessing from "@/app/components/file-manager/hooks/use-processing";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { Input } from "@/app/components/ui/input";
import { useDatasources } from "./hooks/use-datasources";

interface DatasourceItemProps {
  datasource: DatasourceResponse;
  onClick?: () => void;
  onRefresh?: () => void;
}

export function DatasourceItem({ datasource, onClick, onRefresh }: DatasourceItemProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [description, setDescription] = useState(datasource.description || '');
  const [embeddingSettingIdentifier, setEmbeddingSettingIdentifier] = useState(datasource.embedding_setting_identifier || '');
  //const [settings, setSettings] = useState( || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { getDatasource, getAllDatasources, deleteDatasource, createDatasource, updateDatasource } = useDatasources();
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
      await updateDatasource(datasource.identifier, {
        description,
        embedding_setting_identifier: embeddingSettingIdentifier
      });
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
      await deleteDatasource(datasource.identifier);
      onRefresh?.();
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
            {/* embedding identifier text field */}
            <div>
              <label className="text-sm font-medium">Embedding Setting Identifier</label>
              <Input
                className="mt-1"
                value={embeddingSettingIdentifier}
                onChange={(e) => setEmbeddingSettingIdentifier(e.target.value)}
                placeholder="Enter embedding setting identifier..."
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