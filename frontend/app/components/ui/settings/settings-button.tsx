import { Settings } from "lucide-react";
import { Button } from "../button";

interface SettingsButtonProps {
  onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
  const handleClick = () => {
    console.log("Settings button clicked");
    onClick();
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
      onClick={handleClick}
    >
      <Settings className="h-5 w-5" />
      <span className="sr-only">Settings</span>
    </Button>
  );
}
