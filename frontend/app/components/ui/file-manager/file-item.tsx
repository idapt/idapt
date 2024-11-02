"use client";

import { File, Folder, MoreVertical } from "lucide-react";
import { Button } from "../button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";
import { cn } from "../lib/utils";
import { FileIcon } from "../document-preview";

interface FileItemProps {
  name: string;
  type: "file" | "folder";
  size?: string;
  modified?: string;
}

export function FileItem({ name, type, size, modified }: FileItemProps) {
  const Icon = type === "folder" ? Folder : File;
  const extension = name.split(".").pop()?.toLowerCase() || "";

  return (
    <div className="group relative flex items-center space-x-4 p-2 hover:bg-gray-50 rounded-lg">
      <div className="relative h-10 w-10 shrink-0 overflow-hidden rounded-md flex items-center justify-center">
        {type === "folder" ? (
          <Icon className="h-8 w-8 text-blue-500" />
        ) : (
          <img
            className="h-full w-auto object-contain"
            src={FileIcon[extension as keyof typeof FileIcon]}
            alt={`${extension} file`}
          />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{name}</p>
        {size && <p className="text-sm text-gray-500">{size}</p>}
      </div>
      {modified && (
        <div className="text-sm text-gray-500 hidden group-hover:block">
          {modified}
        </div>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="opacity-0 group-hover:opacity-100"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[200px] p-2">
          <DropdownMenuItem className="cursor-pointer p-2 hover:bg-gray-100 rounded-md">
            Download
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer p-2 hover:bg-gray-100 rounded-md">
            Move
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer p-2 hover:bg-gray-100 rounded-md">
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer p-2 hover:bg-gray-100 rounded-md">
            Details
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer p-2 hover:bg-gray-100 rounded-md text-red-600">
            Move to Trash
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
} 