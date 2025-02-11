"use client";

import { useState } from 'react';
import { Button } from '@/app/components/ui/button';
//import { Input } from '@/app/components/ui/input';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, X, Save, Trash2, Settings2 } from 'lucide-react';
import { useApiClient } from '@/app/lib/api-client';
import { ProcessingStepSelect } from './processing-step-select';
import { ParameterEditor } from './parameter-editor';
import { FileExtensionsInput } from './file-extensions-input';
import { 
  updateProcessingStackRouteApiStacksStacksStackIdentifierPut,
  deleteProcessingStackRouteApiStacksStacksStackIdentifierDelete,
  ProcessingStackStepResponse,
  ProcessingStepResponse,
  ProcessingStackResponse
} from '@/app/client';

interface ProcessingStackEditProps {
  stack: ProcessingStackResponse;
  availableSteps: ProcessingStepResponse[];
  onSave: () => void;
  onDelete: () => void;
}

function SortableStep({ 
  step, 
  onRemove, 
  onParametersChange 
}: { 
  step: ProcessingStackStepResponse; 
  onRemove: (id: number) => void;
  onParametersChange: (id: number, parameters: Record<string, any>) => void;
}) {
  const [showParameters, setShowParameters] = useState(false);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: step.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex flex-col p-2 border rounded mb-2"
    >
      <div className="flex items-center gap-2">
        <div {...attributes} {...listeners}>
          <GripVertical className="h-4 w-4 cursor-grab" />
        </div>
        <div className="flex-1">
          <div className="font-medium">{step.step.display_name}</div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowParameters(!showParameters)}
        >
          <Settings2 className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRemove(step.id)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {showParameters && (
        <div className="mt-4 pl-8">
          <ParameterEditor
            schema={step.step.parameters_schema}
            parameters={step.parameters || []}
            onChange={(parameters) => onParametersChange(step.id, parameters)}
          />
        </div>
      )}
    </div>
  );
}

export function ProcessingStackEdit({ stack, availableSteps, onSave, onDelete }: ProcessingStackEditProps) {
  const [steps, setSteps] = useState<ProcessingStackStepResponse[]>(stack.steps);
  const [extensions, setExtensions] = useState<string[]>(stack.supported_extensions || []);
  const client = useApiClient();

  const handleSave = async () => {
    try {
      await updateProcessingStackRouteApiStacksStacksStackIdentifierPut({
        client,
        path: { stack_identifier: stack.identifier },
        body: {
          steps: steps.map((step, index) => ({
            ...step,
            order: index + 1
          })),
          supported_extensions: extensions
        }
      });
      onSave();
    } catch (error) {
      console.error('Failed to save stack:', error);
      window.alert((error as Error).message || 'Failed to save stack');
    }
  };

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (!over || active.id === over.id) {
      return;
    }

    const activeStep = steps.find(s => s.id === active.id);
    const overStep = steps.find(s => s.id === over.id);

    if (!activeStep || !overStep) return;

    // Prevent moving node parser from first position
    if (activeStep.step.type === 'node_parser' && over.id !== steps[0].id) {
      window.alert('Node parser must remain the first step');
      return;
    }

    // Prevent moving anything before node parser
    if (steps[0].step.type === 'node_parser' && active.id !== steps[0].id && over.id === steps[0].id) {
      window.alert('Cannot move steps before node parser');
      return;
    }

    // Prevent moving embedding from last position
    if (activeStep.step.type === 'embedding' && over.id !== steps[steps.length - 1].id) {
      window.alert('Embedding must remain the last step');
      return;
    }

    // Prevent moving anything after embedding
    const embeddingIndex = steps.findIndex(s => s.step.type === 'embedding');
    if (embeddingIndex !== -1 && active.id !== steps[embeddingIndex].id && over.id === steps[embeddingIndex].id) {
      window.alert('Cannot move steps after embedding');
      return;
    }

    setSteps((items) => {
      const oldIndex = items.findIndex((item) => item.id === active.id);
      const newIndex = items.findIndex((item) => item.id === over.id);

      return arrayMove(items, oldIndex, newIndex).map((item, index) => ({
        ...item,
        order: index + 1,
      }));
    });
  };

  const handleRemoveStep = (stepId: number) => {
    setSteps(prevSteps => {
      const filteredSteps = prevSteps.filter(s => s.id !== stepId);
      return filteredSteps.map((step, index) => ({
        ...step,
        order: index + 1,
      }));
    });
  };

  const validateStepAddition = (newStep: ProcessingStepResponse, currentSteps: ProcessingStackStepResponse[]): string | null => {
    // Check for node_parser - must be first and only one
    if (newStep.type === 'node_parser') {
      if (currentSteps.length > 0 && currentSteps[0].step.type !== 'node_parser') {
        return 'Node parser must be the first step in the stack';
      }
      if (currentSteps.some(s => s.step.type === 'node_parser')) {
        return 'Only one node parser is allowed per stack';
      }
    }

    // Check for embedding - must be last and only one
    if (newStep.type === 'embedding') {
      if (currentSteps.some(s => s.step.type === 'embedding')) {
        return 'Only one embedding step is allowed per stack';
      }
      // If there are other steps after where this would be inserted
      if (currentSteps.length > currentSteps.length) {
        return 'Embedding step must be the last step in the stack';
      }
    }

    // Node post processors can be added anywhere between parser and embedding
    if (newStep.type === 'node_post_processor') {
      const hasEmbedding = currentSteps.some(s => s.step.type === 'embedding');
      if (hasEmbedding && currentSteps[currentSteps.length - 1].step.type === 'embedding') {
        return 'Cannot add post processor after embedding step';
      }
    }

    return null;
  };

  const handleAddStep = (step: ProcessingStepResponse) => {
    const validationError = validateStepAddition(step, steps);
    if (validationError) {
      window.alert(validationError);
      return;
    }

    const newStep: ProcessingStackStepResponse = {
      id: Math.max(0, ...steps.map(s => s.id)) + 1,
      step,
      step_identifier: step.identifier,
      order: steps.length + 1,
      parameters: {},
    };

    // If it's a node parser, add it to the beginning
    if (step.type === 'node_parser') {
      setSteps([newStep, ...steps.map(s => ({ ...s, order: s.order + 1 }))]);
    }
    // If it's an embedding, add it to the end
    else if (step.type === 'embedding') {
      setSteps([...steps, newStep]);
    }
    // For post processors, add them before any embedding step
    else {
      const embeddingIndex = steps.findIndex(s => s.step.type === 'embedding');
      if (embeddingIndex === -1) {
        setSteps([...steps, newStep]);
      } else {
        const newSteps = [...steps];
        newSteps.splice(embeddingIndex, 0, newStep);
        setSteps(newSteps.map((s, i) => ({ ...s, order: i + 1 })));
      }
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this processing stack? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteProcessingStackRouteApiStacksStacksStackIdentifierDelete({
        client,
        path: { stack_identifier: stack.identifier }
      });
      onDelete();
    } catch (error) {
      console.error('Failed to delete stack:', error);
      window.alert((error as Error).message || 'Failed to delete stack');
    }
  };

  const handleParametersChange = (stepId: number, parameters: Record<string, any>) => {
    setSteps(prevSteps => 
      prevSteps.map(step => 
        step.id === stepId 
          ? { ...step, parameters }
          : step
      )
    );
  };

  return (
    <div className="space-y-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={steps}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-2">
            {steps.map((step) => (
              <SortableStep 
                key={step.id} 
                step={step} 
                onRemove={handleRemoveStep}
                onParametersChange={handleParametersChange}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <ProcessingStepSelect 
            availableSteps={availableSteps} 
            onStepSelect={handleAddStep}
          />
        </div>
      </div>

      <FileExtensionsInput
        value={extensions}
        onChange={setExtensions}
      />

    <div className="flex justify-between items-center"> 
      <Button variant="destructive" onClick={handleDelete}>
        <Trash2 className="h-4 w-4 mr-2" />
        Delete Stack
      </Button>
      <Button onClick={handleSave}>
        <Save className="h-4 w-4 mr-2" />
        Save Changes
        </Button>
      </div>
    </div>
  );
}