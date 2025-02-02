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
      // Pack the files together by datasources in a list of list of ProcessingItem
      const processFiles: ProcessingItem[][] = [];
      const datasources: string[] = [];
      for (const file of files) { 
        const datasourceName = file.split('/')[0];
        if (!datasources.includes(datasourceName)) {
          datasources.push(datasourceName);
          processFiles.push([]);
        }
        processFiles[datasources.indexOf(datasourceName)].push({
          original_path: file,
          stacks_identifiers_to_queue: [stackIdentifier]
        });
      } 
      for (const datasourceName in processFiles) {
        const response = await processingRouteApiProcessingPost({
          client,
          body: { items: processFiles[datasourceName] },
          query: { user_id: userId, datasource_name: datasourceName }
        });
        if (response.error) {
          throw new Error(response.error.detail?.[0]?.msg || 'Unknown error');
        }
      }
    } catch (error) {
      console.error('Processing error:', error);
      throw error;
    }
  };

  return { processWithStack };
}

export default useProcessing;