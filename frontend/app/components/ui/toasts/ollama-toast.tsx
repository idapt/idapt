import { CheckCircle, Loader2 } from "lucide-react";
import { OllamaToastItem } from '@/app/types/toast';
import { BaseToast } from "../file-manager/base-toast";
import { useToastContext } from '@/app/contexts/toast-context';
import { useState, useEffect, useRef } from "react";
import { useOllamaStatus } from '@/app/hooks/use-ollama-status';
import { useOllamaToast } from '@/app/hooks/use-ollama-toast';

export function OllamaToast() {
  const { items } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);
  const { isDownloading } = useOllamaStatus();
  const { startDownloading, stopDownloading } = useOllamaToast();
  const prevIsDownloadingRef = useRef(isDownloading);

  const ollamaItem = items.find((item): item is OllamaToastItem => 
    item.type === 'ollama'
  );

  useEffect(() => {
    if (isDownloading !== prevIsDownloadingRef.current) {
      if (isDownloading) {
        startDownloading();
      } else {
        stopDownloading();
      }
      prevIsDownloadingRef.current = isDownloading;
    }
  }, [isDownloading, startDownloading, stopDownloading]);
  
  if (!ollamaItem) {
    return null;
  }

  return (
    <BaseToast
      title="Ollama status"
      progress={0}
      isMinimized={isMinimized}
      total={0}
      completed={0}
      onMinimize={() => setIsMinimized(!isMinimized)}
    >
      <div className="px-3 py-2">
        <div className="flex items-center gap-2">
          {isDownloading ? (
            <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />
          ) : (
            <CheckCircle className="h-3 w-3 flex-shrink-0" />
          )}
          <span className="text-xs">
            Waiting for ollama to be reachable and have the selected model downloaded. <br />
            Check if the ollama host url is correctly set up in the settings and if when you access it in your browser, you see &quot;Ollama is running&quot;. <br />
            Any file upload and processing attempts done while you see this toast will be queued and processed once the provider is ready and a new file is uploaded.
          </span>
        </div>
      </div>
    </BaseToast>
  );
} 