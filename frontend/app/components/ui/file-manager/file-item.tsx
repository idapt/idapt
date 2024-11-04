"use client";

import { File, Folder } from "lucide-react";
import { Button } from "../button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";

interface FileItemProps {
  name: string;
  type: "file" | "folder";
  size?: string;
  modified?: string;
  onClick?: () => void;
}

export function FileItem({ name, type, size, modified, onClick }: FileItemProps) {
  return (
    <div 
      className="flex items-center p-2 hover:bg-gray-100 rounded cursor-pointer"
      onClick={onClick}
    >
      {type === 'folder' ? (
        <Folder className="w-4 h-4 mr-2 text-blue-500" />
      ) : (
        <File className="w-4 h-4 mr-2 text-gray-500" />
      )}
      <span className="text-sm truncate w-full" title={name}>{name}</span>
    </div>
  );
} 