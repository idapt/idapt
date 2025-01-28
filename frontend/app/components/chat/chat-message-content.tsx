import {
  ChatMessage,
  ContentPosition,
  getSourceAnnotationData,
  useChatMessage,
  useChatUI,
} from "@llamaindex/chat-ui";
import { DeepResearchCard } from "@/app/components/chat/custom/deep-research-card";
import { Markdown } from "@/app/components/chat/custom/markdown";
import { ToolAnnotations } from "@/app/components/chat/tools/chat-tools";

export function ChatMessageContent() {
  const { isLoading, append } = useChatUI();
  const { message } = useChatMessage();
  const customContent = [
    {
      // override the default markdown component
      position: ContentPosition.MARKDOWN,
      component: (
        <Markdown
          content={message.content}
          sources={getSourceAnnotationData(message.annotations)?.[0]}
        />
      ),
    },
    // add the deep research card
    {
      position: ContentPosition.CHAT_EVENTS,
      component: <DeepResearchCard message={message} />,
    },
    {
      // add the tool annotations after events
      position: ContentPosition.AFTER_EVENTS,
      component: <ToolAnnotations message={message} />,
    },
  ];
  return (
    <ChatMessage.Content
      content={customContent}
      isLoading={isLoading}
      append={append}
    />
  );
}
