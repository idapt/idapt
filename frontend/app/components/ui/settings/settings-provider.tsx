"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface SettingsContextType {
  isOpen: boolean;
  openSettings: () => void;
  closeSettings: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const openSettings = () => setIsOpen(true);
  const closeSettings = () => setIsOpen(false);

  return (
    <SettingsContext.Provider value={{ isOpen, openSettings, closeSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
} 