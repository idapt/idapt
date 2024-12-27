'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { ToastItem } from '@/app/types/toast';

interface ToastContextType {
  items: ToastItem[];
  totalItems: number;
  addItems: (items: ToastItem[]) => void;
  updateItem: (id: string, updates: Partial<Omit<ToastItem, 'type'>>) => void;
  removeItem: (id: string) => void;
  cancelAll: () => void;
  resetAll: () => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const [totalItems, setTotalItems] = useState(0);

  const addItems = (newItems: ToastItem[]) => {
    setItems(prev => [...prev, ...newItems]);
    setTotalItems(prev => prev + newItems.length);
  };

  const updateItem = (id: string, updates: Partial<Omit<ToastItem, 'type'>>) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ));
  };

  const removeItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
    setTotalItems(prev => Math.max(0, prev - 1));
  };

  const cancelAll = () => {
    window.dispatchEvent(new CustomEvent('cancelAllOperations'));
    setItems([]);
    setTotalItems(0);
  };

  const resetAll = () => {
    setItems([]);
    setTotalItems(0);
  };

  return (
    <ToastContext.Provider value={{
      items,
      totalItems,
      addItems,
      updateItem,
      removeItem,
      cancelAll,
      resetAll,
    }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
} 