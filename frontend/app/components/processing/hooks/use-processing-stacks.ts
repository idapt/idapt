import { useState, useEffect, useCallback } from 'react';
import { useApiClient } from '@/app/lib/api-client';
import { 
  getProcessingStacksRouteApiStacksStacksGet,
  getProcessingStepsRouteApiStacksStepsGet,
  ProcessingStackResponse, 
  ProcessingStepResponse
} from '@/app/client';
import { useProcessingStacksState } from '@/app/components/processing/hooks/use-processing-stacks-state';

export function useProcessingStacks() {
  const [loading, setLoading] = useState(false);
  const client = useApiClient();
  const { setStacks, setSteps } = useProcessingStacksState();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [stacksResponse, stepsResponse] = await Promise.all([
        getProcessingStacksRouteApiStacksStacksGet({
          client,
        }),
        getProcessingStepsRouteApiStacksStepsGet({
          client,
        })
      ]);
      setStacks(stacksResponse.data || []);
      setSteps(stepsResponse.data || []);
    } catch (error) {
      console.error('Error fetching processing stacks:', error);
    } finally {
      setLoading(false);
    }
  }, [client, setStacks, setSteps]);

  const stacks = useProcessingStacksState(state => state.stacks);
  const steps = useProcessingStacksState(state => state.steps);

  return {
    stacks,
    steps,
    loading,
    refetch: fetchData
  };
}