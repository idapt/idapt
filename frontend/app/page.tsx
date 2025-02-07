'use client';

import { Settings } from "@/app/components/settings";
import { Chat } from '@/app/components/chat/chat';
import { DataStreamHandler } from '@/app/components/chat/data-stream-handler';
import { AppSidebar } from '@/app/components/chat/app-sidebar';
import { FileManager } from "@/app/components/file-manager/file-manager";
import { ProcessingStacks } from "@/app/components/processing/processing-stacks";
import { useState, useEffect } from 'react';
import { SidebarToggle } from "./components/chat/sidebar-toggle";
import { AuthForm } from "@/app/components/auth/auth-form";
import { useAuth } from "@/app/components/auth/auth-context";

export type View = 'chat' | 'files' | 'settings' | 'processing';

export default function App() {
  const { isAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<View>('chat');

  useEffect(() => {
    if (!isAuthenticated) {
      setCurrentView('chat');
    }
  }, [isAuthenticated]);

  const renderContent = () => {
    switch (currentView) {
      case 'files':
        return <FileManager />;
      case 'settings':
        return <Settings />;
      case 'processing':
        return <ProcessingStacks />;
      default:
        return (
          <div className="flex-1 h-full w-full">
            <Chat isReadonly={false} />
            <DataStreamHandler />
          </div>
        );
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <AuthForm mode="login" />
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <AppSidebar onViewChange={setCurrentView} currentView={currentView} />
      <div className="flex justify-between pt-1.5 pl-1.5">
        <SidebarToggle />
      </div>
      <main className="flex-1 relative overflow-hidden">
        {renderContent()}
      </main>
    </div>
  );  
}

