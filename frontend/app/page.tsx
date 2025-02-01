'use client';

import { Settings } from "@/app/components/settings";
import { Chat } from '@/app/components/chat/chat';
import { DataStreamHandler } from '@/app/components/chat/data-stream-handler';
import { AppSidebar } from '@/app/components/chat/app-sidebar';
import { useUser } from "@/app/contexts/user-context";
import { FileManager } from "@/app/components/file-manager/file-manager";
import { ProcessingStacks } from "@/app/components/processing/processing-stacks";
import { useState } from 'react';
import { SidebarToggle } from "./components/chat/sidebar-toggle";

type View = 'chat' | 'files' | 'settings' | 'processing';

export default function App() {
  const { userId } = useUser();
  const [currentView, setCurrentView] = useState<View>('chat');

  const renderContent = () => {
    switch (currentView) {
      case 'files':
        return (
          <div className="flex-1 h-full w-full overflow-auto">
            <FileManager />
          </div>
        );
      case 'settings':
        return (
          <div className="flex-1 h-full w-full p-6 overflow-auto">
            <Settings />
          </div>
        );
      case 'processing':
        return (
          <div className="flex-1 h-full w-full p-6 overflow-auto">
            <ProcessingStacks />
          </div>
        );
      default:
        return (
          <div className="flex-1 h-full w-full">
            <div className="pl-0 h-full">
              <Chat
                isReadonly={false}
              />
              <DataStreamHandler />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <AppSidebar userId={userId} onViewChange={setCurrentView} currentView={currentView} />
      <div className="flex justify-between pt-1.5 pl-1.5">
        <SidebarToggle />
      </div>
      <main className="flex-1 relative overflow-hidden">
        {renderContent()}
      </main>
    </div>
  );
}
