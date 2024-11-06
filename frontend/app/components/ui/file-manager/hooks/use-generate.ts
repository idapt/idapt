import { useClientConfig } from "../../chat/hooks/use-config";
import { useState } from "react";

export function useGenerate() {
  const { backend } = useClientConfig();
  const [isGenerating, setIsGenerating] = useState(false);

  const generate = async (filePaths: string[]) => {
    try {
      setIsGenerating(true);
      const response = await fetch(`${backend}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_paths: filePaths }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate');
      }
      
      return data;
    } catch (error) {
      console.error('Generation error:', error);
      throw error;
    } finally {
      setIsGenerating(false);
    }
  };

  return { generate, isGenerating };
} 