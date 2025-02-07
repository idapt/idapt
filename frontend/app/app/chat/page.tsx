'use client';

import { Chat } from '@/app/components/chat/chat';
import { DataStreamHandler } from '@/app/components/chat/data-stream-handler';

export default function ChatPage() {
  return (
    <div className="flex-1 h-full w-full">
      <Chat isReadonly={false} />
      <DataStreamHandler />
    </div>
  );
} 