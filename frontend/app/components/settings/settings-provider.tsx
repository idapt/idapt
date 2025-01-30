"use client";

import { createContext, useContext } from "react";
import { useSettingsAPI } from "@/app/components/settings/hooks/use-settings";

interface SettingsContextType {
  getSetting: ReturnType<typeof useSettingsAPI>['getSetting'];
  getAllSettings: ReturnType<typeof useSettingsAPI>['getAllSettings'];
  updateSetting: ReturnType<typeof useSettingsAPI>['updateSetting'];
  createSetting: ReturnType<typeof useSettingsAPI>['createSetting'];
  deleteSetting: ReturnType<typeof useSettingsAPI>['deleteSetting'];
  isLoading: boolean;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const settingsAPI = useSettingsAPI();

  return (
    <SettingsContext.Provider value={settingsAPI}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettingsContext() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
} 