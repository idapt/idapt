import { useState, useEffect, useRef } from 'react';
import { Loader2 } from "lucide-react";
import { useProcessingStatus } from '@/app/hooks/use-processing-status';
import { useProcessingToast } from '@/app/hooks/use-processing-toast';
import { BaseToast } from "../file-manager/base-toast";
import { useToastContext } from '@/app/contexts/toast-context';
import { ProcessingToastItem } from '@/app/types/toast';

export function ProcessingToast() {
  const { items } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);
  const { status } = useProcessingStatus();
  const { startProcessing, updateProcessing } = useProcessingToast();
  const prevTotalRef = useRef(0);

  const processingItem = items.find((item): item is ProcessingToastItem => 
    item.type === 'processing'
  );

  useEffect(() => {
    if (!status) return;

    const totalFiles = status.queued_count + status.processing_count;
    const prevTotal = prevTotalRef.current;

    if (totalFiles > 0) {
      if (totalFiles !== prevTotal) {
        startProcessing('Processing files', totalFiles);
        prevTotalRef.current = totalFiles;
      }
      
      if (processingItem && processingItem.processed !== status.processing_count) {
        updateProcessing('global-processing-status', status.processing_count, totalFiles);
      }
    }
  }, [status?.queued_count, status?.processing_count, startProcessing, updateProcessing, processingItem]);

  if (!processingItem) {
    return null;
  }

  return (
    <BaseToast
      title="Processing Files"
      progress={processingItem.progress}
      total={processingItem.total}
      completed={processingItem.processed}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
    >
      <div className="max-h-[240px] overflow-y-auto">
        {status?.processing_files?.map((file) => (
          <ProcessingItem
            key={file.path}
            name={file.name}
            status="processing"
          />
        ))}
        {status?.queued_files?.map((file) => (
          <ProcessingItem
            key={file.path}
            name={file.name}
            status="pending"
          />
        ))}
      </div>
    </BaseToast>
  );
}

function ProcessingItem({ name, status }: { name: string; status: 'processing' | 'pending' }) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex justify-between items-center gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {status === 'processing' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {status === 'pending' && <div className="h-3 w-3 bg-gray-200 rounded-full flex-shrink-0" />}
          <span className="text-xs truncate">{name}</span>
        </div>
      </div>
    </div>
  );
} 