"use client";

import { SettingsButton } from "@/app/components/settings/settings-button";
import { SettingsDialog } from "@/app/components/settings/settings-dialog";
import { useSettings } from "@/app/components/settings/settings-provider";

export function Settings() {
  const { isOpen, openSettings, closeSettings } = useSettings();
    
  return (
    <>
      <SettingsButton onClick={openSettings} />
      {isOpen && (
        <SettingsDialog 
          isOpen={isOpen} 
          onClose={closeSettings} 
        />
      )}
    </>
  );
} 