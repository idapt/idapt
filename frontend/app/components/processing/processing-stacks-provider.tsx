"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface ProcessingStacksContextType {
  isOpen: boolean;
  openProcessingStacks: () => void;
  closeProcessingStacks: () => void;
}

const ProcessingStacksContext = createContext<ProcessingStacksContextType | undefined>(undefined);

export function ProcessingStacksProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const openProcessingStacks = () => setIsOpen(true);
  const closeProcessingStacks = () => setIsOpen(false);

  return (
    <ProcessingStacksContext.Provider value={{ isOpen, openProcessingStacks, closeProcessingStacks }}>
      {children}
    </ProcessingStacksContext.Provider>
  );
}

export function useProcessingStacksDialog() {
  const context = useContext(ProcessingStacksContext);
  if (context === undefined) {
    throw new Error("useProcessingStacksDialog must be used within a ProcessingStacksProvider");
  }
  return context;
} 