"use client";

import { SettingsButton } from "./settings-button";
import { SettingsDialog } from "./settings-dialog";
import { useSettings } from "./settings-provider";

export function Settings() {
  const { isOpen, openSettings, closeSettings } = useSettings();
  
  console.log("Settings render - isOpen:", isOpen);
  
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