import { useToastContext } from '@/app/contexts/toast-context';
import { DeletionToastItem } from '@/app/types/toast';

export function useDeletionToast() {
  const { addItems, updateItem, removeItem } = useToastContext();

  const startDeletion = (name: string, path: string) => {
    const id = crypto.randomUUID();
    addItems([{
      id,
      name,
      path,
      status: 'processing' as const,
      progress: 0,
      type: 'deletion' as const
    }]);
    return id;
  };

  const completeDeletion = (id: string) => {
    updateItem(id, {
      status: 'completed' as const,
      progress: 100,
    });
  };

  const failDeletion = (id: string) => {
    updateItem(id, {
      status: 'error' as const,
      progress: 0,
    });
  };

  return {
    startDeletion,
    completeDeletion,
    failDeletion
  };
} 