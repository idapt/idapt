'use client';

import { Settings } from "@/app/components/settings";

import SettingsLayout from "./layout";

export default function SettingsPage() {
  return (
    <SettingsLayout>
      <div className="flex-1 h-full w-full">
        <Settings />
      </div>
    </SettingsLayout>
  );
} 