import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import { Progress } from "@/app/components/ui/progress";
import { UploadToastItem } from "@/app/types/toast";
import { useToastContext } from "@/app/contexts/toast-context";
import { BaseToast } from "@/app/components/file-manager/base-toast";

export function UploadToast() {
  const { items, removeItem, resetAll } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);
  
  const uploadItems = items.filter((item): item is UploadToastItem => 
    item.type === 'upload'
  );
  
  const activeUploads = uploadItems.filter(item => 
    item.status === 'processing' || item.status === 'pending'
  );
  
  const completedUploads = uploadItems.filter(item => 
    item.status === 'completed'
  );

  // Auto-hide and reset when all uploads are complete
  useEffect(() => {
    if (uploadItems.length > 0 && activeUploads.length === 0) {
      const timer = setTimeout(() => {
        resetAll();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [uploadItems.length, activeUploads.length, resetAll]);

  if (uploadItems.length === 0) {
    return null;
  }

  // Calculate total progress based on all items including completed ones
  const totalProgress = uploadItems.reduce((acc, item) => acc + item.progress, 0);
  const progress = Math.round(totalProgress / uploadItems.length);
  const total = uploadItems.length;

  return (
    <BaseToast
      title="File Uploads"
      progress={progress}
      total={total}
      completed={completedUploads.length}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
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

function UploadItem({ item, onCancel }: { item: UploadToastItem; onCancel: () => void }) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex justify-between items-center gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {item.status === 'processing' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {item.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />}
          {item.status === 'error' && <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="text-xs truncate">{item.name}</span>
        </div>
        {item.status === 'processing' && (
          <Button variant="ghost" size="icon" className="h-5 w-5" onClick={onCancel}>
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>
      {item.status === 'processing' && (
        <Progress value={item.progress} className="h-1 mt-1" />
      )}
    </div>
  );
}