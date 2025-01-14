export interface ProcessingStepParameter {
  name: string;
  type: string;
  description?: string;
  default?: any;
}

export interface ProcessingStep {
  identifier: string;
  display_name: string;
  description?: string;
  type: string;
  parameters_schema: Record<string, any>;
}

export interface ProcessingStackStep {
  id: number;
  step: ProcessingStep;
  order: number;
  parameters: Record<string, any>;
  step_identifier: string;
}

export interface ProcessingStack {
  identifier: string;
  display_name: string;
  description?: string;
  is_enabled: boolean;
  steps: ProcessingStackStep[];
}