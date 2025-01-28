"use client";

import { ChatMessage, ChatMessages, useChatUI } from "@llamaindex/chat-ui";
import { ChatMessageAvatar } from "@/app/components/chat/chat-avatar";
import { ChatMessageContent } from "@/app/components/chat/chat-message-content";
import { ChatStarter } from "@/app/components/chat/chat-starter";

export default function CustomChatMessages() {
  const { messages } = useChatUI();
  return (
    <ChatMessages className="shadow-xl rounded-xl">
      <ChatMessages.List>
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            message={message}
            isLast={index === messages.length - 1}
          >
            <ChatMessageAvatar />
            <ChatMessageContent />
            <ChatMessage.Actions />
          </ChatMessage>
        ))}
        <ChatMessages.Loading />
      </ChatMessages.List>
      <ChatMessages.Actions />
      <ChatStarter />
    </ChatMessages>
  );
}
