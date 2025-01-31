import { CheckCircle, Loader2, XCircle } from "lucide-react";
import { OllamaToastItem } from '@/app/types/toast';
import { BaseToast } from "@/app/components/file-manager/base-toast";
import { useToastContext } from '@/app/contexts/toast-context';
import { useState, useEffect, useRef } from "react";
import { useOllamaStatus } from '@/app/components/toasts/hooks/use-ollama-status';

interface OllamaToastProps {
  isDownloading: boolean;
  onClose?: () => void;
}

export function OllamaToast({ isDownloading, onClose }: OllamaToastProps) {
  const { items } = useToastContext();
  const [isMinimized, setIsMinimized] = useState(false);

  const ollamaItem = items.find((item): item is OllamaToastItem => 
    item.type === 'ollama'
  );
  
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
      onClose={onClose}
    >
      <div className="px-3 py-2">
        <div className="flex items-center gap-2">
          {isDownloading ? (
            <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />
          ) : (
            <CheckCircle className="h-3 w-3 flex-shrink-0" />
          )}
          <span className="text-xs">
            At least one of your ollama servers is unreachable. <br />
            Check if the ollama host url is correctly set up in the settings and datasources settings. <br /> 
            Do not add trailing slashes to the url, use http if you did not set up https for your ollama server and use OLLAMA_HOST=0.0.0.0 if you want to access it from outside your local network. <br />
            Check if when you access it in your browser, you see &quot;Ollama is running&quot;. <br />
            Any processing attempts done while you see this toast will be queued and processed once the provider is ready you trigger processing for a file.
          </span>
        </div>
      </div>
    </BaseToast>
  );
} 