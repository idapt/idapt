import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Plus } from 'lucide-react';
import { ProcessingStepResponse } from '@/app/client';

interface ProcessingStepSelectProps {
  availableSteps: ProcessingStepResponse[];
  onStepSelect: (step: ProcessingStepResponse) => void;
}

export function ProcessingStepSelect({ availableSteps, onStepSelect }: ProcessingStepSelectProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Plus className="h-4 w-4 mr-2" />
          Add Step
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Processing Step</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4">
          {availableSteps.map((step) => (
            <Button
              key={step.identifier}
              variant="outline"
              className="justify-start"
              onClick={() => onStepSelect(step)}
            >
              <div className="text-left">
                <div className="font-medium">{step.display_name}</div>
                <div className="text-sm text-muted-foreground">{step.description}</div>
              </div>
            </Button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
} 