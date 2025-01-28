import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Button } from '../ui/button';
import { Plus } from 'lucide-react';
import { ProcessingStep } from '@/app/components/processing/processing';

interface ProcessingStepSelectProps {
  availableSteps: ProcessingStep[];
  onStepSelect: (step: ProcessingStep) => void;
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