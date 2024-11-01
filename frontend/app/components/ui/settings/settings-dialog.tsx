import { X } from "lucide-react";
import { Button } from "../button";
import { useGenerate } from "./hooks/use-generate";
import { useState } from "react";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [error, setError] = useState<string | null>(null);
  const { generate, isGenerating } = useGenerate();

  const handleGenerate = async () => {
    try {
      setError(null);
      const result = await generate();
      if (result.status === 'success') {
        alert('Data generated successfully!');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to generate data');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Dialog */}
      <div className="relative bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold m-0">Settings</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </Button>
        </div>
        
        {/* Add settings content here */}
        <div className="space-y-4">
          {error && (
            <div className="text-red-500 text-sm">{error}</div>
          )}
          <Button 
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full"
          >
            {isGenerating ? 'Generating...' : 'Generate Data'}
          </Button>
        </div>
      </div>
    </div>
  );
} 