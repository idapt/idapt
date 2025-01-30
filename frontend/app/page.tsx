'use client';

import Header from "@/app/components/header";
import { Settings } from "@/app/components/settings";
import { NavMenu } from "@/app/components/nav/nav-menu";
import { Chat } from '@/app/components/chat/chat';
import { generateUUID } from '@/app/lib/utils';
import { DataStreamHandler } from '@/app/components/chat/data-stream-handler';
import { AppSidebar } from '@/app/components/chat/app-sidebar';
import { SidebarInset } from '@/app/components/ui/sidebar';
import { useUser } from "@/app/contexts/user-context";

export default function App() {
  const { userId } = useUser();
  const chat_frontend_uuid = generateUUID();

  return (
    <>
      <AppSidebar userId={userId} />
      <SidebarInset>
        <Settings />
        <NavMenu />
        <Header />
        <Chat
          key={chat_frontend_uuid}
          id={chat_frontend_uuid}
          initialMessages={[]}
          //selectedModelId={selectedModelId}
          //selectedVisibilityType="private"
          isReadonly={false}
        />
        <DataStreamHandler id={chat_frontend_uuid} />
      </SidebarInset>
    </>
  );
}
