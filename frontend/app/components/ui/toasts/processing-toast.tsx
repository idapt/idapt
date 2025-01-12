import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { ProcessingToastItem } from '@/app/types/toast';
import { useToastContext } from '@/app/contexts/toast-context';
import { BaseToast } from "../file-manager/base-toast";

interface ProcessingFile {
  name: string;
  path: string;
}

interface ProcessingStatus {
  queued_count: number;
  processing_count: number;
  queued_files: ProcessingFile[];
  processing_files: ProcessingFile[];
}

export function ProcessingToast() {
  const { items, resetAll } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/generate/status');
        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch processing status:', error);
        // Set status to null to handle the error state
        setStatus(null);
      }
    };

    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  // Hide toast when no files are being processed or queued
  // Also handle the case when status is null (error state)
  if (!status || (status.queued_count === 0 && status.processing_count === 0)) {
    return null;
  }

  const totalFiles = status.queued_count + status.processing_count;
  const progress = Math.round((0 / totalFiles) * 100);

  return (
    <BaseToast
      title="Processing Files"
      progress={progress}
      total={totalFiles}
      completed={0}
      isMinimized={isMinimized}
      onMinimize={() => setIsMinimized(!isMinimized)}
    >
      <div className="max-h-[240px] overflow-y-auto">
        {status.processing_files?.map((file) => (
          <ProcessingItem
            key={file.path}
            name={file.name}
            status="processing"
          />
        ))}
        {status.queued_files?.map((file) => (
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