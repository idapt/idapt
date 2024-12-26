import { X, XCircle, Loader2, CheckCircle2, AlertCircle, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "../button";
import { Progress } from "../progress";
import { useUploadStore } from "@/app/stores/upload-store";
import type { UploadItem } from "@/app/stores/upload-store";
import { useState } from "react";

export function UploadToast() {
  const { items, totalItems, removeItem, cancelAll } = useUploadStore();
  const [isMinimized, setIsMinimized] = useState(false);
  
  const activeUploads = items.filter(item => item.status !== 'completed' && item.status !== 'error');
  const completedUploads = items.filter(item => item.status === 'completed');
  
  if (items.length === 0) return null;

  // Calculate global progress
  const globalProgress = Math.round(
    (completedUploads.length / totalItems) * 100
  );

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white rounded-lg shadow-lg">
      <div className="p-3 border-b flex justify-between items-center">
        <span className="text-sm font-medium">File Uploads</span>
        <div className="flex gap-1">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6" 
            onClick={() => setIsMinimized(!isMinimized)}
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6" 
            onClick={cancelAll}
          >
            <XCircle className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {!isMinimized && (
        <div className="max-h-[240px] overflow-y-auto">
          {activeUploads.map((item) => (
            <UploadItem
              key={item.id}
              item={item}
              onCancel={() => removeItem(item.id)}
            />
          ))}
        </div>
      )}

      <div className="p-3 border-t bg-gray-50">
        <div className="flex justify-between items-center text-xs text-gray-500 mb-1">
          <span>Overall Progress</span>
          <span>{globalProgress}% ({completedUploads.length}/{totalItems})</span>
        </div>
        <Progress value={globalProgress} className="h-1" />
      </div>
    </div>
  );
}

function UploadItem({ item, onCancel }: { item: UploadItem; onCancel: () => void }) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex justify-between items-center gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {item.status === 'uploading' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {item.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />}
          {item.status === 'error' && <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="text-xs truncate">{item.name}</span>
        </div>
        {item.status === 'uploading' && (
          <Button variant="ghost" size="icon" className="h-5 w-5" onClick={onCancel}>
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>
      {item.status === 'uploading' && (
        <Progress value={item.progress} className="h-1 mt-1" />
      )}
    </div>
  );
} 