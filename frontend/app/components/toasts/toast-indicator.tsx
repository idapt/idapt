import { useState } from 'react';
import { Button } from "@/app/components/ui/button";
import { AlertCircle, Upload, Trash2, Loader2, CheckCircle } from "lucide-react";
import { useToastContext } from '@/app/contexts/toast-context';
import { OllamaToast } from './ollama-toast';
import { UploadToast } from './upload-toast';
import { DeletionToast } from './deletion-toast';
import { ProcessingToast } from './processing-toast';
import { useOllamaContext } from '@/app/contexts/ollama-context';
import { useProcessingContext } from '@/app/contexts/processing-context';

export function ToastIndicator() {
  const { items } = useToastContext();
  const [activeToast, setActiveToast] = useState<string | null>(null);
  
  const { isDownloading, showOllamaToast, hideOllamaToast, isToastVisible } = useOllamaContext();
  const { status: processingStatus, showProcessingToast, hideProcessingToast } = useProcessingContext();
  
  const ollamaItem = items.find(item => item.type === 'ollama');

  const uploadItems = items.filter(item => item.type === 'upload');
  const deletionItems = items.filter(item => item.type === 'deletion');
  const processingItems = items.filter(item => item.type === 'processing');
  
  const getUploadIconColor = () => {
    if (uploadItems.some(item => item.status === 'error')) return 'text-red-500';
    if (uploadItems.every(item => item.status === 'completed')) return 'text-green-500';
    return 'text-foreground';
  };

  const getDeletionIconColor = () => {
    if (deletionItems.some(item => item.status === 'error')) return 'text-red-500';
    if (deletionItems.every(item => item.status === 'completed')) return 'text-green-500';
    return 'text-foreground';
  };

  const getProcessingIconColor = () => {
    if (processingStatus?.processing_items?.some(item => item.status === 'error')) return 'text-red-500';
    if (processingStatus?.processing_items?.every(item => item.status === 'completed')) return 'text-green-500';
    return 'text-foreground';
  };

  const handleOllamaClick = () => {
    if (activeToast === 'ollama') {
      hideOllamaToast();
      setActiveToast(null);
    } else {
      showOllamaToast();
      setActiveToast('ollama');
    }
  };

  const handleProcessingClick = () => {
    if (activeToast === 'processing') {
      hideProcessingToast();
      setActiveToast(null);
    } else {
      showProcessingToast();
      setActiveToast('processing');
    }
  };

  if (!ollamaItem && !uploadItems.length && !deletionItems.length && !processingItems.length && !isDownloading && (processingStatus?.queued_count === 0 && processingStatus?.processing_count === 0)) {
    return null;
  }

  return (
    <div>
      {/* Display the toasts above the indicators */}
      {activeToast === 'ollama' && (
        <OllamaToast 
          isDownloading={isDownloading}
          onClose={() => {
            hideOllamaToast();
            setActiveToast(null);
          }} 
        />
      )}
      
      {activeToast === 'upload' && (
        <UploadToast />
      )}
      
      {activeToast === 'deletion' && (
        <DeletionToast />
      )}
      
      {activeToast === 'processing' && (
        <ProcessingToast 
          onClose={() => {
            hideProcessingToast();
            setActiveToast(null);
          }} 
        />
      )}

      <div className="flex gap-2 p-2">
        {(isToastVisible || isDownloading) && (
          <Button
            variant="ghost"
            size="icon"
            className={`h-8 w-8 ${activeToast === 'ollama' ? 'bg-accent' : ''}`}
            onClick={handleOllamaClick}
          >
            <AlertCircle className="h-4 w-4 text-yellow-500" />
          </Button>
        )}
        
        {uploadItems.length > 0 && (
          <Button
            variant="ghost"
            size="icon"
            className={`h-8 w-8 ${activeToast === 'upload' ? 'bg-accent' : ''}`}
            onClick={() => setActiveToast(activeToast === 'upload' ? null : 'upload')}
          >
            <Upload className={`h-4 w-4 ${getUploadIconColor()}`} />
          </Button>
        )}

        {deletionItems.length > 0 && (
          <Button
            variant="ghost"
            size="icon"
            className={`h-8 w-8 ${activeToast === 'deletion' ? 'bg-accent' : ''}`}
            onClick={() => setActiveToast(activeToast === 'deletion' ? null : 'deletion')}
          >
            <Trash2 className={`h-4 w-4 ${getDeletionIconColor()}`} />
          </Button>
        )}

        {((processingStatus?.queued_count || 0) > 0 || (processingStatus?.processing_count || 0) > 0) && (
          <Button
            variant="ghost"
            size="icon"
            className={`h-8 w-8 ${activeToast === 'processing' ? 'bg-accent' : ''}`}
            onClick={handleProcessingClick}
          >
            {processingStatus?.processing_items?.some(item => item.status === 'processing') ? (
              <Loader2 className={`h-4 w-4 animate-spin ${getProcessingIconColor()}`} />
            ) : (
              <CheckCircle className={`h-4 w-4 ${getProcessingIconColor()}`} />
            )}
          </Button>
        )}
      </div>
    </div>
  );
} 