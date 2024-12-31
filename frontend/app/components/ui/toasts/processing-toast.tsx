import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { ProcessingToastItem } from '@/app/types/toast';
import { useToastContext } from '@/app/contexts/toast-context';
import { BaseToast } from "../file-manager/base-toast";

export function ProcessingToast() {
  const { items, resetAll } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);
  
  const processingItems = items.filter((item): item is ProcessingToastItem => 
    item.type === 'processing'
  );
  
  const activeProcessing = processingItems.filter(item => 
    item.status === 'processing'
  );
  
  const completedProcessing = processingItems.filter(item => 
    item.status === 'completed'
  );

  // Auto-hide and reset when all processing is complete
  useEffect(() => {
    if (activeProcessing.length === 0 && completedProcessing.length > 0) {
      const timer = setTimeout(() => {
        if (processingItems.every(item => item.total === item.processed)) {
          resetAll();
        }
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [activeProcessing.length, completedProcessing.length, processingItems, resetAll]);

  if (activeProcessing.length === 0 && completedProcessing.length === 0) {
    return null;
  }

  const totalProcessing = processingItems.reduce((acc, item) => acc + item.total, 0);
  const totalProcessed = processingItems.reduce((acc, item) => acc + item.processed, 0);
  const progress = Math.round((totalProcessed / totalProcessing) * 100);

  return (
    <BaseToast
      title="Processing Files"
      progress={progress}
      total={totalProcessing}
      completed={totalProcessed}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
    >
      <div className="max-h-[240px] overflow-y-auto">
        {activeProcessing.map((item) => (
          <ProcessingItem
            key={item.id}
            item={item}
          />
        ))}
      </div>
    </BaseToast>
  );
}

function ProcessingItem({ item }: { item: ProcessingToastItem }) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex justify-between items-center gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {item.status === 'processing' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {item.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />}
          {item.status === 'error' && <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="text-xs truncate">{item.name}</span>
        </div>
        <span className="text-xs text-gray-500">
          {item.processed}/{item.total}
        </span>
      </div>
    </div>
  );
} 