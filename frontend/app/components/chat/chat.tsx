'use client';

import type { Attachment } from 'ai';
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
import { useUser } from "@/app/contexts/user-context";
import { convertToUIMessages } from '@/app/lib/utils';
import { useChatResponse } from '@/app/contexts/chat-response-context';
import { Block } from './block';

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
  const { userId } = useUser();
  const { currentChatId, currentChat } = useChatResponse();

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
    api: `${backend}/api/chat?user_id=${userId}`,
    headers: {
      "X-User-Id": userId
    },
    id: currentChatId,
    body: { id: currentChatId },
    initialMessages: convertToUIMessages(currentChat?.messages || []),
    experimental_throttle: 100,
    sendExtraMessageFields: true
  });

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
  }, [currentChat, setMessages]);



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
          //userId={userId}
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
              handleSubmit={handleSubmit}
              isLoading={isLoading}
              stop={stop}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              append={append}
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
        append={append}
        messages={messages}
        setMessages={setMessages}
        reload={reload}
        //votes={[]}//{votes}
        isReadonly={isReadonly}
      />}
    </>
  );
}
