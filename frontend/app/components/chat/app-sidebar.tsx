'use client';

import { useRouter, usePathname } from 'next/navigation';
import { MessageSquare, Folder, Settings as SettingsIcon, Database } from 'lucide-react';
import { SidebarHistory } from '@/app/components/chat/sidebar-history';
import { Button } from '@/app/components/ui/button';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  useSidebar,
} from '@/app/components/ui/sidebar';
import { SidebarUserNav } from '@/app/components/chat/sidebar-user-nav';
import Header from '@/app/components/header';
import { ToastIndicator } from '@/app/components/toasts/toast-indicator';
import { useAuth } from '../auth/auth-context';
import { View } from '@/app/page';

interface AppSidebarProps {
  onViewChange: (view: View) => void;
  currentView: View;
}

export function AppSidebar({ onViewChange, currentView }: AppSidebarProps) {
  const { setOpenMobile } = useSidebar();
  
  return (
    <Sidebar className="group-data-[side=left]:border-r-0">
      <SidebarHeader>
        <Header />
        <SidebarMenu>
          <div className="flex flex-col gap-2 px-2">
            <Button
              variant="ghost"
              className={`justify-start gap-2 w-full ${currentView === 'chat' ? 'bg-accent' : ''}`}
              onClick={() => {
                setOpenMobile(false);
                onViewChange('chat');
              }}
            >
              <MessageSquare className="h-4 w-4" />
              Chat
            </Button>
            
            <Button
              variant="ghost"
              className={`justify-start gap-2 w-full ${currentView === 'files' ? 'bg-accent' : ''}`}
              onClick={() => {
                setOpenMobile(false);
                onViewChange('files');
              }}
            >
              <Folder className="h-4 w-4" />
              Files
            </Button>

            <Button
              variant="ghost"
              className={`justify-start gap-2 w-full ${currentView === 'settings' ? 'bg-accent' : ''}`}
              onClick={() => {
                setOpenMobile(false);
                onViewChange('settings');
              }}
            >
              <SettingsIcon className="h-4 w-4" />
              Settings
            </Button>

            <Button
              variant="ghost"
              className={`justify-start gap-2 w-full ${currentView === 'processing' ? 'bg-accent' : ''}`}
              onClick={() => {
                setOpenMobile(false);
                onViewChange('processing');
              }}
            >
              <Database className="h-4 w-4" />
              Processing Stacks
            </Button>
          </div>
        </SidebarMenu>
      </SidebarHeader>
      
      <div className="h-[1px] bg-border my-2 mx-2" />
      
      <SidebarContent>
        <SidebarHistory setCurrentView={onViewChange} />
      </SidebarContent>

      <SidebarFooter>
        <ToastIndicator />
        <div className="p-2">
          <SidebarUserNav />
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
