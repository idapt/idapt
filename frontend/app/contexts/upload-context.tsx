'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

export interface UploadItem {
  id: string;
  name: string;
  path: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress: number;
}

interface UploadContextType {
  items: UploadItem[];
  totalItems: number;
  addItems: (items: UploadItem[]) => void;
  updateItem: (id: string, updates: Partial<UploadItem>) => void;
  removeItem: (id: string) => void;
  cancelAll: () => void;
}

const UploadContext = createContext<UploadContextType | null>(null);

export function UploadProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [totalItems, setTotalItems] = useState(0);

  const addItems = (newItems: UploadItem[]) => {
    setItems(prev => [...prev, ...newItems]);
    setTotalItems(prev => prev + newItems.length);
  };

  const updateItem = (id: string, updates: Partial<UploadItem>) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ));
  };

  const removeItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  const cancelAll = () => {
    window.dispatchEvent(new CustomEvent('cancelAllUploads'));
    const completedItems = items.filter(item => item.status === 'completed');
    setItems(completedItems);
    setTotalItems(completedItems.length);
  };

  return (
    <UploadContext.Provider value={{
      items,
      totalItems,
      addItems,
      updateItem,
      removeItem,
      cancelAll,
    }}>
      {children}
    </UploadContext.Provider>
  );
}

export function useUploadContext() {
  const context = useContext(UploadContext);
  if (!context) {
    throw new Error('useUploadContext must be used within an UploadProvider');
  }
  return context;
} 