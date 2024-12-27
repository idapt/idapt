import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { DeletionToastItem } from '@/app/types/toast';
import { useToastContext } from '@/app/contexts/toast-context';
import { BaseToast } from "../file-manager/base-toast";

export function DeletionToast() {
  const { items, resetAll } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);
  
  const deletionItems = items.filter((item): item is DeletionToastItem => 
    item.type === 'deletion'
  );
  
  const activeDeletions = deletionItems.filter(item => 
    item.status === 'processing'
  );
  
  const completedDeletions = deletionItems.filter(item => 
    item.status === 'completed'
  );

  // Auto-hide and reset when all deletions are complete
  useEffect(() => {
    if (activeDeletions.length === 0 && completedDeletions.length > 0) {
      const timer = setTimeout(() => {
        resetAll();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [activeDeletions.length, completedDeletions.length, resetAll]);

  if (activeDeletions.length === 0 && completedDeletions.length === 0) {
    return null;
  }

  const totalDeletions = activeDeletions.length + completedDeletions.length;
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
        {activeDeletions.map((item) => (
          <DeletionItem
            key={item.id}
            item={item}
          />
        ))}
      </div>
    </BaseToast>
  );
}

function DeletionItem({ item }: { item: DeletionToastItem }) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex justify-between items-center gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {item.status === 'processing' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {item.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />}
          {item.status === 'error' && <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="text-xs truncate">{item.name}</span>
        </div>
      </div>
    </div>
  );
} 