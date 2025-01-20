"use client";

import { Layers } from "lucide-react";
import { Button } from "@/app/components/ui/button";

interface ProcessingStacksButtonProps {
  onClick: () => void;
}

export function ProcessingStacksButton({ onClick }: ProcessingStacksButtonProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="absolute top-4 right-16 text-gray-500 hover:text-gray-700"
      onClick={onClick}
    >
      <Layers className="h-5 w-5" />
      <span className="sr-only">Processing Stacks</span>
    </Button>
  );
}
