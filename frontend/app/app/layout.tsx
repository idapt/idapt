'use client';

import { AppSidebar } from '@/app/components/app-sidebar';
import { SidebarToggle } from '@/app/components/chat/sidebar-toggle';
import { useAuth } from '@/app/components/auth/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { SettingsProvider } from "@/app/components/settings/settings-provider";
import { ProcessingStacksProvider } from "@/app/components/processing/processing-stacks-provider";
import { SidebarProvider } from '@/app/components/ui/sidebar';
import { OllamaProvider } from '@/app/contexts/ollama-context';
import { ProcessingProvider } from '@/app/contexts/processing-context';
import { ChatProvider } from '@/app/contexts/chat-response-context';
import { ToastContextProvider } from '../contexts/toast-context';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isAuthenticated, router]);

  return (
    <ToastContextProvider>
      <OllamaProvider>
        <ProcessingProvider>
          <ChatProvider>
            <SidebarProvider>
              <ProcessingStacksProvider>
                <div className="flex h-screen w-screen overflow-hidden">
                  <AppSidebar />
                  <div className="flex justify-between pt-1.5 pl-1.5">
                    <SidebarToggle />
                  </div>
                  <main className="flex-1 relative overflow-hidden">
                    {children}
                  </main>
                </div>
              </ProcessingStacksProvider>
            </SidebarProvider>
          </ChatProvider>
        </ProcessingProvider>
      </OllamaProvider>
    </ToastContextProvider>
  );
} 