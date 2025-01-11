"use client";

export interface ChatConfig {
  backend?: string;
}

// This function will return the right backend origin depending on where it is called from.
function getBackendOrigin(): string { 
  // Hosted
  if (process.env.DEPLOYEMENT_TYPE === 'hosted') {
    // Hosted dev
    if (process.env.ENVIRONMENT === 'dev') {
      // Use the localhost address as backend is running with minikube exposed on port 8000
      return `https://localhost`;
    }
    // Hosted prod
    else {
      // Use the api.idapt.ai address
      //return `https://api.idapt.ai`;
      return `https://localhost`;
    }
  }
  // Self-hosted
  else {
    // If this code is executed on the client side / machine.
    if ( typeof window !== 'undefined') {
      // Use the current frontend origin as the backend is hosted at the same address on port 8000.
      return window.location.origin;
    }
    // If this is ran on the server side
    else {
      // Backend is running at localhost:8000
      return `https://localhost`;
    }
  }
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
