"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { useSettings as useSettingsAPI } from "@/app/components/settings/hooks/use-settings";

interface SettingsContextType {
  isOpen: boolean;
  openSettings: () => void;
  closeSettings: () => void;
  getProviderSettings: ReturnType<typeof useSettingsAPI>['getProviderSettings'];
  updateProviderSettings: ReturnType<typeof useSettingsAPI>['updateProviderSettings'];
  isLoading: boolean;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const settingsAPI = useSettingsAPI();

  const openSettings = () => setIsOpen(true);
  const closeSettings = () => setIsOpen(false);

  return (
    <SettingsContext.Provider value={{ 
      isOpen, 
      openSettings, 
      closeSettings,
      ...settingsAPI
    }}>
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