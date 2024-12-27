import { UploadToast } from "./upload-toast";
import { DeletionToast } from "./deletion-toast";
import { ProcessingToast } from "./processing-toast";

export function ToastContainer() {
  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      <UploadToast />
      <ProcessingToast />
      <DeletionToast />
    </div>
  );
} 