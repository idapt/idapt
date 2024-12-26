import { X, XCircle, Loader2 } from "lucide-react";
import { Button } from "../button";
import { Progress } from "../progress";

interface UploadToastProps {
  currentFile: string;
  currentIndex: number;
  totalFiles: number;
  progress: number;
  onCancel: () => void;
}

export function UploadToast({ currentFile, currentIndex, totalFiles, progress, onCancel }: UploadToastProps) {
  return (
    <div className="fixed bottom-4 right-4 w-80 bg-white rounded-lg shadow-lg p-4 space-y-2">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm font-medium">Uploading files...</span>
        </div>
        <Button variant="ghost" size="icon" onClick={onCancel}>
          <XCircle className="h-4 w-4" />
        </Button>
      </div>
      
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-500">
          <span className="truncate">{currentFile}</span>
          <span>{currentIndex} of {totalFiles}</span>
        </div>
        <Progress value={progress} className="h-1" />
      </div>
    </div>
  );
} 