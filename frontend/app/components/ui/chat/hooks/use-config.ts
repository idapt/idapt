"use client";

export interface ChatConfig {
  backend?: string;
}

function getBackendOrigin(): string {  
  // In production, construct URL from HOST_DOMAIN
  const hostDomain = process.env.HOST_DOMAIN;
  const protocol = hostDomain === 'localhost' ? 'http' : 'https';
  return `${protocol}://${hostDomain}`;
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
