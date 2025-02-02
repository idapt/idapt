import { Database, FolderOpen, FolderSync, MessagesSquare } from "lucide-react";

interface DatasourceTypeIconProps {
  type: string;
  className?: string;
}

export function DatasourceTypeIcon({ type, className = "h-12 w-12" }: DatasourceTypeIconProps) {
  return (
    <div className="relative">
      {type === 'CHATS' ? (
        <MessagesSquare className={`${className} text-gray-500`} />
      ) : type === 'FILES' ? (
        <FolderOpen className={`${className} text-gray-500`} />
      ) : type === 'WINDOWS_SYNC' ? (
        <FolderSync className={`${className} text-gray-500`} />
      ) : (
        <Database className={`${className} text-gray-500`} />
      )}
      <Database className="h-5 w-5 text-gray-500 absolute -bottom-1 -right-1 bg-white rounded-full" />
    </div>
  );
} 