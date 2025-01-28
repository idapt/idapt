import { useState, useEffect, useCallback } from 'react';
import { useApiClient } from '@/app/lib/api-client';
import { 
  getProcessingStacksRouteApiStacksStacksGet,
  getProcessingStepsRouteApiStacksStepsGet,
  ProcessingStackResponse, 
  ProcessingStepResponse
} from '@/app/client';
import { useUser } from '@/app/contexts/user-context';

export function useProcessingStacks() {
  const client = useApiClient();
  const { userId } = useUser();
  const [stacks, setStacks] = useState<ProcessingStackResponse[]>([]);
  const [steps, setSteps] = useState<ProcessingStepResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStacks = useCallback(async () => {
    try {
      const response = await getProcessingStacksRouteApiStacksStacksGet({ client, query: { user_id: userId } });
      setStacks(response.data || []);
    } catch (error) {
      console.error('Failed to fetch processing stacks:', error);
      setStacks([]);
    }
  }, [client]);

  const fetchSteps = useCallback(async () => {
    try {
      const response = await getProcessingStepsRouteApiStacksStepsGet({ client, query: { user_id: userId } });
      setSteps(response.data || []);
    } catch (error) {
      console.error('Failed to fetch processing steps:', error);
      setSteps([]);
    }
  }, [client]);

  useEffect(() => {
    Promise.all([fetchStacks(), fetchSteps()]).finally(() => setLoading(false));
  }, [fetchStacks, fetchSteps]);

  return { stacks, steps, loading, refetch: () => Promise.all([fetchStacks(), fetchSteps()]) };
}