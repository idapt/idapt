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
      status: 'pending',
      progress: 0,
      type: 'deletion'
    }]);
    return id;
  };

  const completeDeletion = (id: string) => {
    updateItem(id, {
      status: 'completed',
      progress: 100
    });
  };

  const failDeletion = (id: string) => {
    updateItem(id, {
      status: 'error',
      progress: 0
    });
  };

  return {
    startDeletion,
    completeDeletion,
    failDeletion
  };
} 