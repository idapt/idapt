import { useUploadContext } from "@/app/contexts/upload-context";

export function useDeletionToast() {
  const { addItems, updateItem, removeItem } = useUploadContext();

  const startDeletion = (name: string, path: string) => {
    const id = crypto.randomUUID();
    addItems([{
      id,
      name,
      path,
      status: 'deleting' as const,
      progress: 0,
      _type: 'deletion' as const
    }]);
    return id;
  };

  const completeDeletion = (id: string) => {
    updateItem(id, {
      status: 'completed' as const,
      progress: 100,
      _type: 'deletion' as const
    });
  };

  const failDeletion = (id: string) => {
    updateItem(id, {
      status: 'error' as const,
      progress: 0,
      _type: 'deletion' as const
    });
  };

  return {
    startDeletion,
    completeDeletion,
    failDeletion
  };
} 