'use client';

import { useWindowSize } from 'usehooks-ts';

//import { ModelSelector } from '@/app/components/chat/model-selector';
import { Button } from '@/app/components/ui/button';
import { PlusIcon } from './icons';
//import { useSidebar } from '@/app/components/ui/sidebar';
import { memo } from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/app/components/ui/tooltip';
//import { VisibilityType, VisibilitySelector } from './visibility-selector';
import { useChatResponse } from '@/app/contexts/chat-response-context';
import { generateUUID } from '@/app/lib/utils';

function PureChatHeader({
  //chatId,
  //selectedModelId,
  //selectedVisibilityType,
  //isReadonly,
}: {
  //chatId: string;
  //selectedModelId: string;
  //selectedVisibilityType: VisibilityType;
  //isReadonly: boolean;
}) {
  //const router = useRouter();
  //const { open } = useSidebar();
  //const { width: windowWidth } = useWindowSize();
  const { tryToSetCurrentChat } = useChatResponse();

  return (
    <header className="flex sticky top-0 bg-background py-1.5 items-center px-2 md:px-2 gap-2">
      {(
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              className="order-2 md:order-1 md:px-2 px-2 md:h-fit ml-auto md:ml-0"
              onClick={() => {
                tryToSetCurrentChat(undefined);
                //router.push('/');
                //router.refresh();
              }}
            >
              <PlusIcon />
              <span className="md:sr-only">New Chat</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>New Chat</TooltipContent>
        </Tooltip>
      )}

      {/* {!isReadonly && (
        <ModelSelector
          selectedModelId={selectedModelId}
          className="order-1 md:order-2"
        />
      )*/}

      {/* {!isReadonly && (
        <VisibilitySelector
          chatId={chatId}
          selectedVisibilityType={selectedVisibilityType}
          className="order-1 md:order-3"
        />
      )} */}
    </header>
  );
}

export const ChatHeader = memo(PureChatHeader, /*(prevProps, nextProps) => {
  return prevProps.selectedModelId === nextProps.selectedModelId;
}*/);
