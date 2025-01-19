"use client";

import { useChat } from "ai/react";
import { useState } from "react";
import { ChatInput, ChatMessages } from "./ui/chat";
import { useClientConfig } from "./ui/chat/hooks/use-config";
import { useUser } from "@/app/contexts/user-context";

export default function ChatSection() {
  const { backend } = useClientConfig();
  const { userId } = useUser();
  const [requestData, setRequestData] = useState<any>();
  const {
    messages,
    input,
    isLoading,
    handleSubmit,
    handleInputChange,
    reload,
    stop,
    append,
    setInput,
  } = useChat({
    body: { 
      data: requestData,
      user_id: userId 
    },
    api: `${backend}/api/chat?user_id=${userId}`,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
    },
    onError: (error: unknown) => {
      console.error("Chat error:", error);
      let errorMessage = "Chat error";
      
      if (error instanceof Error) {
        if (error.message.includes("NetworkError")) {
          errorMessage = "Unable to connect to the AI service. Please check if the service is running and accessible.";
        } 
        else if (error.message.includes("ConnectError: All connection attempts failed")) {
          errorMessage = "Unable to connect to the AI model service. Please check if Ollama is running and accessible.";
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
    <div className="space-y-4 w-full h-full flex flex-col">
      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        reload={reload}
        stop={stop}
        append={append}
      />
      <ChatInput
        input={input}
        handleSubmit={handleSubmit}
        handleInputChange={handleInputChange}
        isLoading={isLoading}
        messages={messages}
        append={append}
        setInput={setInput}
        requestParams={{ params: requestData }}
        setRequestData={setRequestData}
      />
    </div>
  );
}
