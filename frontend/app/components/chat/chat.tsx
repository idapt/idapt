'use client';

import type { Attachment, CreateMessage, Message } from 'ai';
import { useChat } from 'ai/react';
import { useState, useEffect } from 'react';

import { ChatHeader } from '@/app/components/chat/chat-header';
//import type { Vote } from '@/app/lib/db/schema';

//import { Block } from './block';
import { MultimodalInput } from './multimodal-input';
import { Messages } from './messages';
//import { VisibilityType } from './visibility-selector';
import { useBlockSelector } from '@/app/hooks/use-block';
import { useClientConfig } from '../../hooks/use-config';
import { convertToUIMessages } from '@/app/lib/utils';
import { useChatResponse } from '@/app/contexts/chat-response-context';
import { Block } from './block';
import { useAuth } from '@/app/components/auth/auth-context';

export function Chat({
  //id,
  //initialMessages,
  //selectedModelId,
  //selectedVisibilityType,
  isReadonly,
}: {
  //id: number;
  //initialMessages: Array<Message>;
  //selectedModelId: string;
  //selectedVisibilityType: VisibilityType;
  isReadonly: boolean;
}) {
  const { backend } = useClientConfig();
  const { token } = useAuth();
  const { currentChatId, currentChat, refreshChats, tryToSetCurrentChat } = useChatResponse();

  const {
    messages,
    setMessages,
    handleSubmit,
    input,
    setInput,
    append,
    isLoading,
    stop,
    reload,
  } = useChat({
    api: `${backend}/api/chat?datasource_name=Chats`,
    headers: {
      Authorization: `Bearer ${token}` 
    },
    id: currentChatId,
    body: { 
      id: currentChatId
     },
    initialMessages: convertToUIMessages(currentChat?.messages || []),
    experimental_throttle: 100,
    sendExtraMessageFields: true,
    onFinish: (message) => {
      // Refresh the chat history to update the title and update the order of the chats
      // TODO Make this smarter and work with title change
      // Wait 0.5 seconds before refreshing the chats
      refreshChats();
    }
  });

  const wrappedHandleSubmit = async () => {
    if (currentChat == undefined) {
      // If the current chat is undefined, get and create it
      await tryToSetCurrentChat(currentChatId);
    }
    return await handleSubmit({ preventDefault: () => {} });
  }

  const wrappedAppend = async (message: Message | CreateMessage) => {
    if (currentChat == undefined) {
      // If the current chat is undefined, get and create it
      await tryToSetCurrentChat(currentChatId);
    }
    const res = await append(message);
    refreshChats();
    return res;
  }

  // Update messages when chat data changes
  useEffect(() => {
    if (currentChat?.messages) {
      setMessages(convertToUIMessages(currentChat.messages));
    }
    // Reset the chat if the current chat id is empty
    if (!currentChatId || currentChatId === '') {
      setMessages([]);
      setInput('');
    }
  }, [currentChat, setMessages, setInput, currentChatId]);



  //const { data: votes } = useSWR<Array<Vote>>(
  //  `/api/vote?chatId=${id}`,
  //  fetcher,
  //);

  const [attachments, setAttachments] = useState<Array<Attachment>>([]);
  const isBlockVisible = useBlockSelector((state) => state.isVisible);

  return (
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-background">
        <ChatHeader
          //chatId={id}
          //userUuid={userUuid}
          //backend_url={backend_url}
          //selectedModelId={selectedModelId}
          //selectedVisibilityType={selectedVisibilityType}
          //isReadonly={isReadonly}
        />

        <Messages
          chatId={currentChatId}
          isLoading={isLoading}
          //votes={[]}//{votes}
          messages={messages}
          setMessages={setMessages}
          reload={reload}
          isReadonly={isReadonly}
          isBlockVisible={isBlockVisible}
        />

        <form className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
          {!isReadonly && (
            <MultimodalInput
              chatId={currentChatId}
              input={input}
              setInput={setInput}
              handleSubmit={wrappedHandleSubmit}
              isLoading={isLoading}
              stop={stop}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              append={wrappedAppend}
            />
          )}
        </form>
      </div>

      {<Block
        chatId={currentChatId}
        input={input}
        setInput={setInput}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        stop={stop}
        attachments={attachments}
        setAttachments={setAttachments}
        append={wrappedAppend}
        messages={messages}
        setMessages={setMessages}
        reload={reload}
        //votes={[]}//{votes}
        isReadonly={isReadonly}
      />}
    </>
  );
}
