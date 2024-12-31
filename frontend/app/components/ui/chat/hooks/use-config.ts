"use client";

export interface ChatConfig {
  backend?: string;
}

function getBackendOrigin(): string { 
    const hostDomain = process.env.NEXT_PUBLIC_HOST_DOMAIN;
    return `https://${hostDomain}`;  
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
