import { ChevronRight, Home } from "lucide-react";
import { Button } from "../button";

export function FilePath() {
  return (
    <div className="flex items-center space-x-1 text-sm">
      <Button variant="ghost" size="sm">
        <Home className="h-4 w-4 mr-1" />
        Home
      </Button>
      <ChevronRight className="h-4 w-4 text-gray-500" />
      <Button variant="ghost" size="sm">
        Documents
      </Button>
      <ChevronRight className="h-4 w-4 text-gray-500" />
      <Button variant="ghost" size="sm">
        Pictures
      </Button>
    </div>
  );
} 