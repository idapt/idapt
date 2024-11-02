"use client";

import { MessageSquare, Folder } from "lucide-react";
import { Button } from "../button";
import { usePathname, useRouter } from "next/navigation";

export function NavMenu() {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
      <Button
        variant="ghost"
        size="icon"
        className={`text-gray-500 hover:text-gray-700 ${
          pathname === "/" ? "bg-gray-100" : ""
        }`}
        onClick={() => router.push("/")}
      >
        <MessageSquare className="h-5 w-5" />
        <span className="sr-only">Chat</span>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className={`text-gray-500 hover:text-gray-700 ${
          pathname === "/files" ? "bg-gray-100" : ""
        }`}
        onClick={() => router.push("/files")}
      >
        <Folder className="h-5 w-5" />
        <span className="sr-only">Files</span>
      </Button>
    </div>
  );
}