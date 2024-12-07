"use client";

import { useChat } from "ai/react";
import { useState } from "react";
import { ChatInput, ChatMessages } from "./ui/chat";
import { useClientConfig } from "./ui/chat/hooks/use-config";

export default function ChatSection() {
  const { backend } = useClientConfig();
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
    body: { data: requestData },
    api: `${backend}/api/chat`,
    headers: {
      "Content-Type": "application/json", // using JSON because of vercel/ai 2.2.26
    },
    onError: (error: unknown) => {
      console.error("Chat error:", error);
      let errorMessage = "Chat error";
      
      if (error instanceof Error) {

        // Print pretty error messages if the error is known
        // NetworkError
        console.log(error.message);
        if (error.message.includes("NetworkError")) {
          errorMessage = "Unable to connect to the AI service. Please check if the service is running and accessible.";
        } 
        // ConnectError: All connection attempts failed
        else if (error.message.includes("ConnectError: All connection attempts failed")) {
          errorMessage = "Unable to connect to the AI model service. Please check if Ollama is running and accessible.";
        } 
        // Failed to fetch
        else if (error.message.includes("Failed to fetch")) {
          errorMessage = "Network connection error. Please check your internet connection and try again.";
        } 
        // Unknown error
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
