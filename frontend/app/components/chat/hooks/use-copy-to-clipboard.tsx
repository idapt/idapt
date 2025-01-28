"use client";

import * as React from "react";

export interface useCopyToClipboardProps {
  timeout?: number;
}

export function useCopyToClipboard({
  timeout = 2000,
}: useCopyToClipboardProps) {
  const [isCopied, setIsCopied] = React.useState<Boolean>(false);
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  const copyToClipboard = React.useCallback((value: string) => {
    if (!isClient || !value || !navigator.clipboard?.writeText) {
      return;
    }

    navigator.clipboard.writeText(value).then(() => {
      setIsCopied(true);

      setTimeout(() => {
        setIsCopied(false);
      }, timeout);
    });
  }, [isClient, timeout]);

  return { isCopied, copyToClipboard };
}
