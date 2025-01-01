import { UploadToast } from "./upload-toast";
import { DeletionToast } from "./deletion-toast";
import { ProcessingToast } from "./processing-toast";
import { OllamaToast } from './ollama-toast';

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