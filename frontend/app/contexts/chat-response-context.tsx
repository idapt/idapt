'use client';

import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { Message } from 'ai';
import { ChatResponse } from '@/app/client/types.gen';
import useSWR, { mutate } from 'swr';
import { fetcher, generateUUID } from '@/app/lib/utils';
import { useUser } from './user-context';
import { createChatRouteApiDatasourcesChatsPost, deleteChatRouteApiDatasourcesChatsChatUuidDelete } from '@/app/client/sdk.gen';
import { getChatRouteApiDatasourcesChatsChatUuidGet, getAllChatsRouteApiDatasourcesChatsGet } from '@/app/client/sdk.gen';
import { error } from 'console';

interface ChatContextType {
  currentChatId: string;
  //setCurrentChatId: (id: number) => void;
  tryToSetCurrentChat: (id: string) => Promise<void>;
  chats: ChatResponse[] | undefined;
  currentChat: ChatResponse | undefined;
  isChatsLoading: boolean;
  refreshChats: () => Promise<void>;
  deleteChat: (id: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { userId } = useUser();
  const [currentChatId, setCurrentChatId] = useState<string>(generateUUID());
  const [currentChat, setCurrentChat] = useState<ChatResponse | undefined>(undefined);
  const [chats, setChats] = useState<ChatResponse[] | undefined>();
  const [isChatsLoading, setIsChatsLoading] = useState<boolean>(false);
  //const { data: chats, isLoading: isChatsLoading } = useSWR<ChatResponse[]>(
  //  userId ? `/api/datasources/chats?user_id=${userId}` : null,
  //  fetcher
  //);

  /*const { data: currentChat, isChatsLoading: isChatLoading } = useSWR<ChatResponseOutput>(
    currentChatId ? `/api/datasources/chats/${currentChatId}?user_id=${userId}&include_messages=true` : null,
    fetcher
  );*/

    
  useEffect(() => {
    refreshChats();
  }, []);

  const tryToSetCurrentChat = async (uuid: string) => {
    try {
      // Try to get the chat with this id
      const chat = await getChatRouteApiDatasourcesChatsChatUuidGet({
        path: {
        chat_uuid: uuid
        },
        query: {
          user_id: userId,
          datasource_identifier: "Chats",
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
      //await mutate(`/api/datasources/chats?user_id=${userId}`);
      const response = await getAllChatsRouteApiDatasourcesChatsGet({
        query: {
          user_id: userId,
          datasource_identifier: "Chats"
        }
      });
      setChats(response.data);
    } catch (error) {
      alert('Failed to refresh chats');
      console.error('Failed to refresh chats:', error);
    }
  }

  const deleteChat = async (uuid: string) => {
    try {

      if (uuid === currentChatId) {
        // Create a new chat and set it as the current chat before deleting the current one
        await tryToSetCurrentChat(generateUUID());
      }
      await deleteChatRouteApiDatasourcesChatsChatUuidDelete({
        path: {
          chat_uuid: uuid
      },
        query: {
          user_id: userId,
          datasource_identifier: "Chats"
        }
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