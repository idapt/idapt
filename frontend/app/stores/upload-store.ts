import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UploadItem {
  id: string;
  name: string;
  path: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress: number;
}

interface UploadStore {
  items: UploadItem[];
  totalItems: number;
  addItems: (items: Omit<UploadItem, 'id' | 'status' | 'progress'>[]) => void;
  updateItem: (id: string, updates: Partial<UploadItem>) => void;
  removeItem: (id: string) => void;
  clearCompleted: () => void;
  reset: () => void;
  cancelAll: () => void;
  cleanupPendingUploads: () => void;
}

export const useUploadStore = create<UploadStore>()(
  persist(
    (set, get) => ({
      items: [],
      totalItems: 0,
      addItems: (newItems) => {
        const items = newItems.map(item => ({
          ...item,
          id: crypto.randomUUID(),
          status: 'pending' as const,
          progress: 0,
        }));
        set(state => ({ 
          items: [...state.items, ...items],
          totalItems: state.totalItems + items.length
        }));
      },
      updateItem: (id, updates) => {
        set(state => ({
          items: state.items.map(item =>
            item.id === id ? { ...item, ...updates } : item
          ),
        }));
      },
      removeItem: (id) => {
        set(state => ({
          items: state.items.filter(item => item.id !== id)
        }));
      },
      clearCompleted: () => {
        set(state => ({
          items: state.items.filter(item => item.status !== 'completed')
        }));
      },
      reset: () => set({ items: [], totalItems: 0 }),
      cancelAll: () => {
        const items = get().items;
        const pendingItems = items.filter(item => 
          item.status === 'uploading' || item.status === 'pending'
        );
        pendingItems.forEach(item => {
          get().updateItem(item.id, { status: 'error', progress: 0 });
        });
        // Signal that we want to cancel all uploads
        window.dispatchEvent(new CustomEvent('cancelAllUploads'));
      },
      cleanupPendingUploads: () => {
        set(state => ({
          items: state.items.filter(item => 
            item.status !== 'pending' && item.status !== 'uploading'
          )
        }));
      },
    }),
    {
      name: 'upload-store',
    }
  )
); 