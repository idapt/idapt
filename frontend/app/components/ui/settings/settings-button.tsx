import { Settings } from "lucide-react";
import { Button } from "../button";

interface SettingsButtonProps {
  onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="absolute top-4 left-4 text-gray-500 hover:text-gray-700"
      onClick={onClick}
    >
      <Settings className="h-5 w-5" />
      <span className="sr-only">Settings</span>
    </Button>
  );
}
