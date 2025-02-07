'use client';

import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { Message } from 'ai';
import { ChatResponse } from '@/app/client/types.gen';
import useSWR, { mutate } from 'swr';
import { fetcher, generateUUID } from '@/app/lib/utils';
import { createChatRouteApiDatasourcesDatasourceNameChatsPost, deleteChatRouteApiDatasourcesDatasourceNameChatsChatUuidDelete } from '@/app/client/sdk.gen';
import { getChatRouteApiDatasourcesDatasourceNameChatsChatUuidGet, getAllChatsRouteApiDatasourcesDatasourceNameChatsGet } from '@/app/client/sdk.gen';
import { error } from 'console';

interface ChatContextType {
  currentChatId: string;
  tryToSetCurrentChat: (id: string | undefined) => Promise<void>;
  chats: ChatResponse[] | undefined;
  currentChat: ChatResponse | undefined;
  isChatsLoading: boolean;
  refreshChats: () => Promise<void>;
  deleteChat: (id: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [currentChatId, setCurrentChatId] = useState<string>(generateUUID());
  const [currentChat, setCurrentChat] = useState<ChatResponse | undefined>(undefined);
  const [chats, setChats] = useState<ChatResponse[] | undefined>();
  const [isChatsLoading, setIsChatsLoading] = useState<boolean>(false);
  //const { data: chats, isLoading: isChatsLoading } = useSWR<ChatResponse[]>(
  //  userUuid ? `/api/datasources/chats?user_uuid=${userUuid}` : null,
  //  fetcher
  //);

  /*const { data: currentChat, isChatsLoading: isChatLoading } = useSWR<ChatResponseOutput>(
    currentChatId ? `/api/datasources/chats/${currentChatId}?user_uuid=${userUuid}&include_messages=true` : null,
    fetcher
  );*/

    
  useEffect(() => {
    refreshChats();
  }, []);

  const tryToSetCurrentChat = async (uuid: string | undefined) => {
    try {
      if (uuid == undefined) {
        uuid = generateUUID();
      }
      // Try to get the chat with this id
      const chat = await getChatRouteApiDatasourcesDatasourceNameChatsChatUuidGet({
        path: {
        chat_uuid: uuid,
        datasource_name: "Chats"
        },
        query: {
          include_messages: true,
          create_if_not_found: true,
          update_last_opened_at: true
        }
      });
      if (chat.data) {
        setCurrentChatId(uuid);
        setCurrentChat(chat.data);
      }
      // If the chat is not in the list of chats, refresh the chats
      if (!chats?.some(chat => chat.uuid === uuid)) {
        await refreshChats();
      }
    } catch (error) {
      alert('Failed to get chat');
      console.error('Failed to get chat:', error);
    }
  };

  const refreshChats = async () => {
    try {
      setIsChatsLoading(true);
      //await mutate(`/api/datasources/chats?user_uuid=${userUuid}`);
      const response = await getAllChatsRouteApiDatasourcesDatasourceNameChatsGet({
        path: {
          datasource_name: "Chats"
        },
      });
      setChats(response.data);
      setIsChatsLoading(false);
    } catch (error) {
      alert('Failed to refresh chats');
      console.error('Failed to refresh chats:', error);
    }
  }

  const deleteChat = async (uuid: string) => {
    try {

      if (uuid === currentChatId) {
        // Create a new chat and set it as the current chat before deleting the current one
        setCurrentChatId(generateUUID());
        setCurrentChat(undefined);
      }
      await deleteChatRouteApiDatasourcesDatasourceNameChatsChatUuidDelete({
        path: {
          chat_uuid: uuid,
          datasource_name: "Chats"
      },
      });
      await refreshChats();
    } catch (error) {
      alert('Failed to delete chat');
      console.error('Failed to delete chat:', error);
    }
  }

  return (
    <ChatContext.Provider
      value={{
        currentChatId,
        tryToSetCurrentChat,
        chats,
        currentChat,
        isChatsLoading,
        refreshChats,
        deleteChat
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatResponse() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatResponse must be used within a ChatProvider');
  }
  return context;
} 