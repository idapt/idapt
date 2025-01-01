import { Loader2 } from "lucide-react";
import { OllamaToastItem } from '@/app/types/toast';
import { BaseToast } from "../file-manager/base-toast";
import { useToastContext } from '@/app/contexts/toast-context';
export function OllamaToast() {
  const { items } = useToastContext();
  
  const ollamaItem = items.find((item): item is OllamaToastItem => 
    item.type === 'ollama'
  );
  
  if (!ollamaItem) {
    return null;
  }

  return (
    <BaseToast
      title="AI Model Download"
      progress={50}
      isMinimized={false}
      total={0}
      completed={2}
      onMinimize={() => {}}
    >
      <div className="px-3 py-2">
        <div className="flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />
          <span className="text-xs">Downloading AI model...</span>
        </div>
      </div>
    </BaseToast>
  );
} 