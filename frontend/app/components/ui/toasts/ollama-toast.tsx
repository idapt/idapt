import { Loader2 } from "lucide-react";
import { OllamaToastItem } from '@/app/types/toast';
import { BaseToast } from "../file-manager/base-toast";
import { useToastContext } from '@/app/contexts/toast-context';
import { useState } from "react";
export function OllamaToast() {
  const { items } = useToastContext();
  
  
  const ollamaItem = items.find((item): item is OllamaToastItem => 
    item.type === 'ollama'
  );
  
  if (!ollamaItem) {
    return null;
  }

  const [isMinimized, setIsMinimized] = useState(false);

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
          <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />
          <span className="text-xs">Waiting for ollama to be reachable and have the selected model downloaded. <br /> Check if the ollama host url is correctly setup in the settings and if when you access it in your browser, you see "Ollama is running". <br /> Any file upload and processing attempts done while you see this toast will be queued and processed once the provider is ready and a new file is uploaded.</span>
        </div>
      </div>
    </BaseToast>
  );
} 