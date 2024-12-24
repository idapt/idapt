import { AppSettings } from "../types/settings";

export async function getSettings(): Promise<AppSettings> {
  const response = await fetch("/api/settings");
  if (!response.ok) {
    throw new Error("Failed to fetch settings");
  }
  return response.json();
}

export async function updateSettings(settings: AppSettings): Promise<void> {
  const response = await fetch("/api/settings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw errorData;
  }
}