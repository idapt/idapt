import { useState, useEffect } from 'react';
import { useClientConfig } from '@/app/components/ui/chat/hooks/use-config';
import { useApiClient } from '@/app/lib/api-client';
import { ProcessingStack, ProcessingStep } from '@/app/types/processing';

export function useProcessingStacks() {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();
  const [stacks, setStacks] = useState<ProcessingStack[]>([]);
  const [steps, setSteps] = useState<ProcessingStep[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStacks = async () => {
    try {
      const response = await fetchWithAuth(`${backend}/api/stacks/stacks`);
      const data = await response.json();
      setStacks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch processing stacks:', error);
      setStacks([]);
    }
  };

  const fetchSteps = async () => {
    try {
      const response = await fetchWithAuth(`${backend}/api/stacks/steps`);
      const data = await response.json();
      setSteps(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch processing steps:', error);
      setSteps([]);
    }
  };

  useEffect(() => {
    Promise.all([fetchStacks(), fetchSteps()]).finally(() => setLoading(false));
  }, []);

  return { stacks, steps, loading, refetch: () => Promise.all([fetchStacks(), fetchSteps()]) };
}