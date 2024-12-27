import { ReactNode } from 'react';
import { Button } from "../button";
import { Progress } from "../progress";
import { Minimize2, Maximize2, XCircle } from "lucide-react";

interface BaseToastProps {
  title: string;
  progress: number;
  total: number;
  completed: number;
  isMinimized: boolean;
  onMinimize: () => void;
  onCancel?: () => void;
  children: ReactNode;
}

export function BaseToast({
  title,
  progress,
  total,
  completed,
  isMinimized,
  onMinimize,
  onCancel,
  children
}: BaseToastProps) {
  return (
    <div className="w-96 bg-white rounded-lg shadow-lg">
      <div className="p-3 border-b flex justify-between items-center">
        <span className="text-sm font-medium">{title}</span>
        <div className="flex gap-1">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6" 
            onClick={onMinimize}
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </Button>
          {onCancel && (
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-6 w-6" 
              onClick={onCancel}
            >
              <XCircle className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {!isMinimized && children}

      <div className="p-3 border-t bg-gray-50">
        <div className="flex justify-between items-center text-xs text-gray-500 mb-1">
          <span>{progress}% ({completed}/{total})</span>
        </div>
        <Progress value={progress} className="h-1" />
      </div>
    </div>
  );
} 