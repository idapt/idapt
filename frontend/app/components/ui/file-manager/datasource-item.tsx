import { Database, MoreVertical, Settings, Trash2 } from "lucide-react";
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
import { Datasource } from "@/app/types/files";
import { encodePathSafe } from "./utils/path-encoding";

interface DatasourceItemProps {
  datasource: Datasource;
  onClick?: () => void;
  onRefresh?: () => void;
}

export function DatasourceItem({ 
  datasource,
  onClick,
  onRefresh
}: DatasourceItemProps) {
  const { backend } = useClientConfig();
  const [showSettings, setShowSettings] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState<{ x: number; y: number } | null>(null);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenuPosition({ x: e.clientX, y: e.clientY });
  };

  const handleClick = (e: React.MouseEvent) => {
    if (!(e.target as HTMLElement).closest('.dropdown-trigger')) {
      onClick?.();
    }
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setContextMenuPosition(null);
    
    if (confirm(`Are you sure you want to delete datasource "${datasource.name}"?`)) {
      try {
        const encodedName = encodePathSafe(datasource.name);
        const response = await fetch(`${backend}/api/datasources/${encodedName}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error('Failed to delete datasource');
        }
        
        onRefresh?.();
      } catch (error) {
        console.error('Delete failed:', error);
        alert('Failed to delete datasource');
      }
    }
  };

  const handleSettingsClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setContextMenuPosition(null);
    setShowSettings(true);
  };

  return (
    <>
      <div 
        className="group relative flex items-center space-x-4 p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
        onClick={handleClick}
        onContextMenu={handleContextMenu}
      >
        <Database className="h-8 w-8 text-gray-400" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{datasource.name}</p>
          <p className="text-xs text-gray-500">Datasource</p>
        </div>
        
        {/* Regular dropdown menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 dropdown-trigger"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={handleSettingsClick}>
              <Settings className="h-4 w-4 mr-2" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={handleDelete} className="text-red-600">
              <Trash2 className="h-4 w-4 mr-2" />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Context menu (right-click) */}
        {contextMenuPosition && (
          <DropdownMenu 
            open={true} 
            onOpenChange={() => setContextMenuPosition(null)}
          >
            <DropdownMenuContent
              style={{
                position: 'fixed',
                left: contextMenuPosition.x,
                top: contextMenuPosition.y,
              }}
            >
              <DropdownMenuItem onSelect={handleSettingsClick}>
                <Settings className="h-4 w-4 mr-2" />
                <span>Settings</span>
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={handleDelete} className="text-red-600">
                <Trash2 className="h-4 w-4 mr-2" />
                <span>Delete</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Datasource Settings</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 p-4">
            <p><strong>Name:</strong> {datasource.name}</p>
            <p><strong>Type:</strong> {datasource.type}</p>
            <p><strong>Created:</strong> {new Date(datasource.created_at).toLocaleString()}</p>
            <p><strong>Updated:</strong> {new Date(datasource.updated_at).toLocaleString()}</p>
            {datasource.settings && (
              <div>
                <strong>Settings:</strong>
                <pre className="bg-gray-100 p-2 rounded mt-1">
                  {JSON.stringify(datasource.settings, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 