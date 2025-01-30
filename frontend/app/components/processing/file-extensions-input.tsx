import { X } from "lucide-react";
import { useState, KeyboardEvent } from "react";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";

interface FileExtensionsInputProps {
  value: string[];
  onChange: (extensions: string[]) => void;
}

export function FileExtensionsInput({ value, onChange }: FileExtensionsInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addExtension = (extension: string) => {
    const cleaned = extension.trim();
    if (!cleaned) return;
    
    // Ensure extension starts with a dot
    const formattedExtension = cleaned.startsWith(".") ? cleaned : `.${cleaned}`;
    
    // Don't add if already exists
    if (value.includes(formattedExtension)) return;
    
    onChange([...value, formattedExtension]);
    setInputValue("");
  };

  const removeExtension = (extension: string) => {
    onChange(value.filter(ext => ext !== extension));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addExtension(inputValue);
    }
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Supported File Extensions</label>
      
      <div className="flex flex-wrap gap-2 min-h-[2.5rem] p-2 border rounded-md bg-background">
        {value.map((extension) => (
          <div
            key={extension}
            className="flex items-center gap-1 bg-secondary px-2 py-1 rounded-md"
          >
            <span className="text-sm">{extension}</span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-4 w-4 p-0 hover:bg-destructive/20"
              onClick={() => removeExtension(extension)}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        ))}
        
        <div className="flex-1 min-w-[200px]">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => addExtension(inputValue)}
            className="border-0 bg-transparent focus-visible:ring-0 px-0 h-7"
            placeholder="Type extension and press Enter..."
          />
        </div>
      </div>
      
      <p className="text-sm text-muted-foreground">
        Press Enter or comma to add. Extensions will automatically start with a dot.
      </p>
    </div>
  );
} 