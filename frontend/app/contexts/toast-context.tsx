'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import { ToastItem } from '@/app/types/toast';

interface ToastContextType {
  items: ToastItem[];
  addItems: (items: ToastItem[]) => void;
  updateItem: (id: string, updates: Partial<ToastItem>) => void;
  removeItem: (id: string) => void;
  resetAll: () => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastContextProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const addItems = useCallback((newItems: ToastItem[]) => {
    setItems(prev => [...prev, ...newItems]);
  }, []);

  const updateItem = useCallback((id: string, updates: Partial<ToastItem>) => {
    setItems(prev => prev.map(item => 
      item.id === id ? { ...item, ...updates } as ToastItem : item
    ));
  }, []);

  const removeItem = useCallback((id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  }, []);

  const resetAll = useCallback(() => {
    setItems([]);
  }, []);

  return (
    <ToastContext.Provider value={{ items, addItems, updateItem, removeItem, resetAll }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastContextProvider');
  }
  return context;
} 