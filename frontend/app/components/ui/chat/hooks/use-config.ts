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
      // For dev we need to go through the docker network
      if (process.env.ENVIRONMENT === 'dev') {
        return `http://idapt-nginx`;
      }
      // For prod we can just use the loopback address as everything is running on the same machine.
      else {
        return `http://127.0.0.1:8000`;
      }
    }
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
