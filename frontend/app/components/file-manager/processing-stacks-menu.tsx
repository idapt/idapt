import { useProcessingStacksState } from '../processing/hooks/use-processing-stacks-state';
import { useProcessing } from './hooks/use-processing';
import { DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuPortal, DropdownMenuSubContent, DropdownMenuItem } from '../ui/dropdown-menu';
import { Settings2 } from 'lucide-react';
import { useCallback, useState } from 'react';

interface ProcessingStacksMenuProps {
  path: string;
  isFolder?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function ProcessingStacksMenu({ path, isFolder = false, onOpenChange }: ProcessingStacksMenuProps) {
  const stacks = useProcessingStacksState(state => state.stacks);
  const { processWithStack } = useProcessing();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleProcess = useCallback(async (stackId: string) => {
    if (isProcessing) return;
    
    try {
      setIsProcessing(true);
      await processWithStack([path], stackId);
      onOpenChange?.(false);
    } catch (error) {
      console.error('Error processing item:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [path, processWithStack, onOpenChange, isProcessing]);

  if (stacks.length === 0) return null;

  return (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger disabled={isProcessing}>
        <Settings2 className="mr-2 h-4 w-4" />
        Process with...
      </DropdownMenuSubTrigger>
      <DropdownMenuPortal>
        <DropdownMenuSubContent>
          {stacks.map((stack) => (
            <DropdownMenuItem
              key={stack.identifier}
              disabled={isProcessing}
              onSelect={(e) => {
                e.preventDefault();
                handleProcess(stack.identifier);
              }}
            >
              {stack.display_name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuSubContent>
      </DropdownMenuPortal>
    </DropdownMenuSub>
  );
} 