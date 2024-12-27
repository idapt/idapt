import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { UploadItem, useUploadContext } from "@/app/contexts/upload-context";
import { useState, useEffect } from "react";
import { BaseToast } from "./base-toast";

export function DeletionToast() {
  const { items, resetAll } = useUploadContext();
  const [isMinimized, setIsMinimized] = useState(false);
  
  const deletingItems = items.filter(item => 
    item.status === 'deleting' && item._type === 'deletion'
  );
  const completedDeletions = items.filter(item => 
    item.status === 'completed' && item._type === 'deletion'
  );

  // Auto-hide and reset when all deletions are complete
  useEffect(() => {
    if (deletingItems.length === 0 && completedDeletions.length > 0) {
      const timer = setTimeout(() => {
        resetAll();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [deletingItems.length, completedDeletions.length, resetAll]);

  if (deletingItems.length === 0 && completedDeletions.length === 0) {
    return null;
  }

  const totalDeletions = deletingItems.length + completedDeletions.length;
  const progress = Math.round(
    (completedDeletions.length / totalDeletions) * 100
  );

  return (
    <BaseToast
      title="Deleting Items"
      progress={progress}
      total={totalDeletions}
      completed={completedDeletions.length}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
    >
      <div className="max-h-[240px] overflow-y-auto">
        {deletingItems.map((item) => (
          <DeletionItem
            key={item.id}
            item={item}
          />
        ))}
      </div>
    </BaseToast>
  );
}

function DeletionItem({ item }: { item: UploadItem }) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex justify-between items-center gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {item.status === 'deleting' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {item.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />}
          {item.status === 'error' && <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="text-xs truncate">{item.name}</span>
        </div>
      </div>
    </div>
  );
} 