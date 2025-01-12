import { useUser } from '../contexts/user-context';
import { useMemo } from 'react';

export function useApiClient() {
  const { userId } = useUser();
  
  const fetchWithAuth = useMemo(() => {
    return async (url: string, options: RequestInit = {}) => {
      const headers = {
        ...options.headers,
        'X-User-Id': userId,
      };

      // Only add user_id as query param if it's not already present
      const urlObj = new URL(url);
      if (!urlObj.searchParams.has('user_id')) {
        urlObj.searchParams.append('user_id', userId);
      }

      return fetch(urlObj.toString(), {
        ...options,
        headers,
      });
    };
  }, [userId]);

  return { fetchWithAuth };
} 