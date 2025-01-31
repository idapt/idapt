import { useState } from 'react';
import { Loader2, X } from "lucide-react";
import { useToastContext } from '@/app/contexts/toast-context';
import { ProcessingToastItem } from '@/app/types/toast';
import { BaseToast } from "@/app/components/file-manager/base-toast";
import { useProcessingContext } from '@/app/contexts/processing-context';

interface ProcessingToastProps {
  onClose?: () => void;
}

export function ProcessingToast({ onClose }: ProcessingToastProps) {
  const { items, removeItem } = useToastContext();
  const { status } = useProcessingContext();
  const [isMinimized, setIsMinimized] = useState(false);

  const processingItem = items.find((item): item is ProcessingToastItem => 
    item.type === 'processing'
  );

  if (!processingItem || !status) {
    return null;
  }

  const totalFiles = status.queued_count + status.processing_count;
  const processedCount = status.processing_items?.filter(
    item => item.status === 'completed'
  ).length || 0;
  const progress = totalFiles > 0 ? Math.round((processedCount / totalFiles) * 100) : 0;

  // Include both current and completed items
  const allItems = [...(status.processing_items || []), ...(status.queued_items || [])];
  const processingFiles = allItems.filter(f => f.status === 'processing');
  const queuedFiles = allItems.filter(f => f.status === 'queued');
  const completedFiles = allItems.filter(f => f.status === 'completed');

  return (
    <BaseToast
      title={`Processing Files (${processedCount}/${totalFiles})`}
      progress={progress}
      total={totalFiles}
      completed={processedCount}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
      onClose={onClose}
    >
      <div className="max-h-[240px] overflow-y-auto space-y-2">
        {processingFiles.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-gray-500 px-3">Processing</div>
            {processingFiles.map((file) => (
              <ProcessingItem 
                key={file.original_path} 
                name={file.name} 
                status="processing"
                stacks={file.queued_stacks} 
              />
            ))}
          </div>
        )}
        
        {queuedFiles.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-gray-500 px-3">Queued</div>
            {queuedFiles.map((file) => (
              <ProcessingItem 
                key={file.original_path} 
                name={file.name} 
                status="queued"
                stacks={file.queued_stacks}
              />
            ))}
          </div>
        )}

        {completedFiles.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-gray-500 px-3">Completed</div>
            {completedFiles.map((file) => (
              <ProcessingItem 
                key={file.original_path} 
                name={file.name} 
                status="completed"
                stacks={file.queued_stacks}
              />
            ))}
          </div>
        )}
      </div>
    </BaseToast>
  );
}

function ProcessingItem({ 
  name, 
  status, 
  stacks 
}: { 
  name: string; 
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'error';
  stacks: string[];
}) {
  return (
    <div className="px-3 py-2 hover:bg-gray-50">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 min-w-0">
          {status === 'processing' && <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />}
          {status === 'pending' && <div className="h-3 w-3 bg-gray-200 rounded-full flex-shrink-0" />}
          {status === 'queued' && <div className="h-3 w-3 bg-gray-200 rounded-full flex-shrink-0" />}
          {status === 'completed' && <div className="h-3 w-3 bg-green-500 rounded-full flex-shrink-0" />}
          {status === 'error' && <div className="h-3 w-3 bg-red-500 rounded-full flex-shrink-0" />}
          <span className="text-xs truncate">{name}</span>
        </div>
        {stacks && stacks.length > 0 && (
          <div className="flex gap-1 flex-wrap pl-5">
            {stacks.map((stack) => (
              <span 
                key={stack} 
                className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded-full text-gray-600"
              >
                {stack}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 