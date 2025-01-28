"use client";

import { Plus } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import { useChat } from "ai/react";
import { useClientConfig } from "@/app/components/chat/hooks/use-config";
import { useUser } from "@/app/contexts/user-context";

export function ResetButton() {
  const { backend } = useClientConfig();
  const { userId } = useUser();
  const { reload } = useChat({
    api: `${backend}/api/chat?user_id=${userId}`,
  });

  const handleReset = () => {
    window.location.reload(); // This will fully reset the chat state
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      className="absolute top-4 left-4 text-gray-500 hover:text-gray-700"
      onClick={handleReset}
    >
      <Plus className="h-5 w-5" />
      <span className="sr-only">New Chat</span>
    </Button>
  );
}