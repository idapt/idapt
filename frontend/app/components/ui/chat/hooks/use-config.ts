"use client";

export interface ChatConfig {
  backend?: string;
}

// This function will return the right backend origin depending on where it is called from.
function getBackendOrigin(): string { 
    // If this code is executed on the client side / machine.
    if ( typeof window !== 'undefined') {
      // Use the current frontend origin as the backend is hosted at the same address, only with /api after as specified in the nginx.conf file.
      return window.location.origin;
    }
    // If this code is executed on the server side, go through the internal docker network to access the backend.
    else {
      return `http://idapt-backend:3030`;
    }
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
