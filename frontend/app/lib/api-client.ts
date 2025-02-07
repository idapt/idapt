import { createClient, createConfig } from '@hey-api/client-fetch';
import { useClientConfig } from '../hooks/use-config';
import { useMemo } from 'react';
import { useAuth } from '../components/auth/auth-context';

export function useApiClient() {
  const { token, logout } = useAuth();
  const { backend } = useClientConfig();
  
  const client = useMemo(() => {
    const client = createClient(createConfig({
      baseUrl: backend,
    }));
    client.interceptors.request.use((request, options) => {
      if (token) {
        request.headers.set('Authorization', `Bearer ${token}`); 
      }
      return request;
    });
    client.interceptors.response.use((response, options) => {
      if (response.status === 401) {
        logout();
      }
      return response;
    });
    return client;
  }, [backend, token, logout]);

  return client;
} 