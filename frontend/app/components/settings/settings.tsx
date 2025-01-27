"use client";

import { SettingsButton } from "@/app/components/settings/settings-button";
import { SettingsDialog } from "@/app/components/settings/settings-dialog";
import { useSettingsContext } from "@/app/components/settings/settings-provider";

export function Settings() {
  const { isOpen, openSettings, closeSettings } = useSettingsContext();
    
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