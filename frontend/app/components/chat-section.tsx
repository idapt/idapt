"use client";

import dynamic from 'next/dynamic';
import { ChatSection as ChatSectionUI } from "@llamaindex/chat-ui";
import "@llamaindex/chat-ui/styles/markdown.css";
import "@llamaindex/chat-ui/styles/pdf.css";
import { useChat } from "ai/react";
import { useClientConfig } from "@/app/components/chat/hooks/use-config";
import { useUser } from "../contexts/user-context";

// Dynamically import components that use client-side only features
const CustomChatInput = dynamic(() => import("@/app/components/chat/chat-input"), {
  ssr: false
});

const CustomChatMessages = dynamic(() => import("@/app/components/chat/chat-messages"), {
  ssr: false
});

export default function ChatSection() {
  const { backend } = useClientConfig();
  const { userId } = useUser();
  const handler = useChat({
    api: `${backend}/api/chat?user_id=${userId}`,
    headers: {
      "Content-Type": "application/json"
    },
    onError: (error: unknown) => {
      console.error("Chat error:", error);
      let errorMessage = "Chat error";
      
      if (error instanceof Error) {
        if (error.message.includes("NetworkError")) {
          errorMessage = "Unable to connect to the AI service. Please check if the service is running and accessible.";
        } 
        else if (error.message.includes("ConnectError: All connection attempts failed")) {
          errorMessage = "Unable to connect to the AI model service. Please check if llm provider is running and accessible.";
        } 
        else if (error.message.includes("Failed to fetch")) {
          errorMessage = "Network connection error. Please check your internet connection and try again.";
        } 
        else { 
          errorMessage = `Unknown chat error: ${error.message}`;
        }
      }
      
      alert(errorMessage);
    },
    sendExtraMessageFields: true,
  });

  return (
    <ChatSectionUI handler={handler} className="w-full h-full">
      <CustomChatMessages />
      <CustomChatInput />
    </ChatSectionUI>
  );
}