import { useApiClient } from '@/app/lib/api-client';
import { 
  processingRouteApiProcessingPost,
  ProcessingRequest,
  ProcessingItem
} from '@/app/client';
import { useUser } from '@/app/contexts/user-context';

export function useProcessing() {
  const client = useApiClient();
  const { userId } = useUser();

  const processWithStack = async (files: string[], stackIdentifier: string) => {
    try {
      const processFiles: ProcessingItem[] = files.map(original_path => ({
        original_path,
        stacks_identifiers_to_queue: [stackIdentifier]
      }));

      const response = await processingRouteApiProcessingPost({
        client,
        body: { items: processFiles },
        query: { user_id: userId }
      });
      
      return response;
    } catch (error) {
      console.error('Processing error:', error);
      throw error;
    }
  };

  const processFolder = async (folderPath: string, stackIdentifier: string) => {
    try {
      const response = await processingRouteApiProcessingPost({
        client,
        body: {
          items: [{
            original_path: folderPath,
            stacks_identifiers_to_queue: [stackIdentifier]
          }]
        },
        query: { user_id: userId }
      });
      
      return response;
    } catch (error) {
      console.error('Processing folder error:', error);
      throw error;
    }
  };

  return { processWithStack, processFolder };
}

export default useProcessing;