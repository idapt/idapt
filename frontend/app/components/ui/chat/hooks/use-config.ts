"use client";

export interface ChatConfig {
  backend?: string;
}

function getBackendOrigin(): string {
  // We use nginx to route requests to the backend container via the docker network.
  // This is done to secure the backend behind a reverse proxy and avoid cross-origin issues with the frontend, it will see the backend adress as localhost and not cause problems.
  // Use the current frontend origin as the backend is hosted at the same address, only with /api after as specified in the nginx.conf file.
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  // Default to localhost but this should never happen.
  return "http://localhost:3030";
}

export function useClientConfig(): ChatConfig {
  return {
    backend: getBackendOrigin(),
  };
}
