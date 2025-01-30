import { createClient, createConfig } from '@hey-api/client-fetch';
import { useUser } from '../contexts/user-context';
import { useClientConfig } from '../hooks/use-config';
import { useMemo } from 'react';

export function useApiClient() {
  const { userId } = useUser();
  const { backend } = useClientConfig();
  
  const client = useMemo(() => {
    return createClient(createConfig({
      baseUrl: backend,
      headers: {
        'X-User-Id': userId
      }
    }));
  }, [backend, userId]);

  return client;
} 