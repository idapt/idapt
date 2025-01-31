import { create } from 'zustand';
import { ProcessingStackResponse, ProcessingStepResponse } from '@/app/client';

interface ProcessingStacksState {
  stacks: ProcessingStackResponse[];
  steps: ProcessingStepResponse[];
  setStacks: (stacks: ProcessingStackResponse[]) => void;
  setSteps: (steps: ProcessingStepResponse[]) => void;
}

export const useProcessingStacksState = create<ProcessingStacksState>((set) => ({
  stacks: [],
  steps: [],
  setStacks: (stacks) => set({ stacks }),
  setSteps: (steps) => set({ steps })
})); 