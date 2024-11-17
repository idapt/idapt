"use client";

export interface ChatConfig {
  backend?: string;
}

function getBackendOrigin(): string {
  // This code is executed on the client side / machine.
  // Use the current frontend origin as the backend is hosted at the same address, only with /api after as specified in the nginx.conf file.
  if ( typeof window !== 'undefined') {
    return window.location.origin;
  }
  return "http://localhost:3030"; // TODO : Find a better way as this will not work.
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
