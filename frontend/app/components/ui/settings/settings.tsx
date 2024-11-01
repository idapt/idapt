"use client";

import { SettingsButton } from "./settings-button";
import { SettingsDialog } from "./settings-dialog";
import { useSettings } from "./settings-provider";

export function Settings() {
  const { isOpen, openSettings, closeSettings } = useSettings();

  return (
    <>
      <SettingsButton onClick={openSettings} />
      <SettingsDialog isOpen={isOpen} onClose={closeSettings} />
    </>
  );
} 