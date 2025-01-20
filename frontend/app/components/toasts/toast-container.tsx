import { UploadToast } from "@/app/components/toasts/upload-toast";
import { DeletionToast } from "@/app/components/toasts/deletion-toast";
import { ProcessingToast } from "@/app/components/toasts/processing-toast";
import { OllamaToast } from "@/app/components/toasts/ollama-toast";

export function ToastContainer() {
  return (
    <div className="fixed bottom-0 right-0 z-50 m-4 flex flex-col gap-2">
      <UploadToast />
      <DeletionToast />
      <ProcessingToast />
      <OllamaToast />
    </div>
  );
} 