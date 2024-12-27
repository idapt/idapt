import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";
import { Button } from "../button";
import { Progress } from "../progress";
import { UploadToastItem } from '@/app/types/toast';
import { useToastContext } from '@/app/contexts/toast-context';
import { BaseToast } from "../file-manager/base-toast";

export function UploadToast() {
  const { items, totalItems, removeItem, cancelAll, resetAll } = useToastContext();
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
    if (activeUploads.length === 0 && completedUploads.length > 0) {
      const timer = setTimeout(() => {
        resetAll();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [activeUploads.length, completedUploads.length, resetAll]);

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