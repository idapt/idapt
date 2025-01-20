import { useToastContext } from '@/app/contexts/toast-context';
import { UploadToastItem } from '@/app/types/toast';

export function useUploadToast() {
  const { addItems, updateItem, removeItem } = useToastContext();

  const startUpload = (name: string, path: string) => {
    const id = crypto.randomUUID();
    addItems([{
      id,
      name,
      path,
      status: 'pending',
      progress: 0,
      type: 'upload'
    }]);
    return id;
  };

  const updateUpload = (id: string, progress: number) => {
    updateItem(id, {
      status: 'processing',
      progress
    });
  };

  const completeUpload = (id: string) => {
    updateItem(id, {
      status: 'completed',
      progress: 100
    });
  };

  const failUpload = (id: string) => {
    updateItem(id, {
      status: 'error',
      progress: 0
    });
  };

  return {
    startUpload,
    updateUpload,
    completeUpload,
    failUpload
  };
} 