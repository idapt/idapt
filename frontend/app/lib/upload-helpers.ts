import { useUser } from '../contexts/user-context';

export async function uploadWithProgress(
  url: string,
  data: any,
  signal: AbortSignal,
  onProgress: (progress: number) => void,
  userId: string
) {
  const urlObj = new URL(url);
  urlObj.searchParams.append('user_id', userId);

  const response = await fetch(urlObj.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId
    },
    body: JSON.stringify(data),
    signal
  });

  return response;
} 