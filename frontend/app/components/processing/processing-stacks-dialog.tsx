"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { useProcessingStacks } from '@/app/components/processing/hooks/use-processing-stacks';
//import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { Settings2, Plus } from 'lucide-react';
import { useState } from 'react';
import { ProcessingStackEdit } from '@/app/components/processing/processing-stack-edit';
import { ProcessingStackCreate } from '@/app/components/processing/processing-stack-create';
import { ProcessingStackResponse, ProcessingStepResponse } from '@/app/client';

export function ProcessingStacksDialog({ 
  isOpen, 
  onClose 
}: { 
  isOpen: boolean;
  onClose: () => void;
}) {
  const { stacks, steps, loading, refetch } = useProcessingStacks();
  const [isCreating, setIsCreating] = useState(false);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <div className="flex justify-between items-center">
            <DialogTitle>Processing Stacks</DialogTitle>
            <Button variant="outline" onClick={() => setIsCreating(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Stack
            </Button>
          </div>
        </DialogHeader>
        
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="grid grid-cols-1 gap-4 overflow-y-auto pr-2">
            {stacks.map((stack: ProcessingStackResponse) => (
              <ProcessingStackCard 
                key={stack.identifier} 
                stack={stack} 
                steps={steps} 
                onUpdate={refetch}
              />
            ))}
          </div>
        )}

        <ProcessingStackCreate
          isOpen={isCreating}
          onClose={() => setIsCreating(false)}
          onCreated={refetch}
        />
      </DialogContent>
    </Dialog>
  );
}

function ProcessingStackCard({ stack, steps, onUpdate }: { 
  stack: ProcessingStackResponse;
  steps: ProcessingStepResponse[];
  onUpdate: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="border rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-medium">{stack.display_name}</h3>
          {stack.supported_extensions && stack.supported_extensions.length > 0 && (
            <div className="text-sm text-muted-foreground mt-1">
              Supports: {stack.supported_extensions.join(', ')}
            </div>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)}>
          <Settings2 className="h-4 w-4" />
        </Button>
      </div>
      
      {isEditing ? (
        <ProcessingStackEdit 
          stack={stack} 
          availableSteps={steps}
          onSave={() => {
            setIsEditing(false);
            onUpdate();
          }}
          onDelete={() => {
            setIsEditing(false);
            onUpdate();
          }}
        />
      ) : (
        <div className="space-y-2">
          {stack.steps.map((step) => (
            <div 
              key={step.id} 
              className="flex items-center justify-between bg-secondary p-2 rounded"
            >
              <span>{step.step.display_name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}