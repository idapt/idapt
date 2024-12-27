import { X, XCircle, Loader2, CheckCircle2, AlertCircle, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "../button";
import { Progress } from "../progress";
import { useUploadContext } from "@/app/contexts/upload-context";
import type { UploadItem } from "@/app/contexts/upload-context";
import { useState, useRef, useEffect } from "react";
import { BaseToast } from "./base-toast";

export function UploadToast() {
  const { items, totalItems, removeItem, cancelAll } = useUploadContext();
  const [isMinimized, setIsMinimized] = useState(false);
  
  const activeUploads = items.filter(item => 
    (item.status === 'uploading' || item.status === 'pending') && 
    item._type === 'upload'
  );
  const completedUploads = items.filter(item => 
    item.status === 'completed' && item._type === 'upload'
  );

  if (activeUploads.length === 0 && completedUploads.length === 0) {
    return null;
  }

  const progress = Math.round(
    (completedUploads.length / totalItems) * 100
  );

  return (
    <BaseToast
      title="File Uploads"
      progress={progress}
      total={totalItems}
      completed={completedUploads.length}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
      onCancel={cancelAll}
    >
      <div className="max-h-[240px] overflow-y-auto">
        {activeUploads.map((item) => (
          <UploadItem
            key={item.id}
            item={item}
            onCancel={() => removeItem(item.id)}
          />
        ))}
      </div>
    </BaseToast>
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
          {item.status === 'deleting' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
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