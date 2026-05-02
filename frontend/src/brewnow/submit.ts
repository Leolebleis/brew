import { apiJson } from "../api/client";

const POLL_WINDOW_MS = 12 * 60 * 1000; // 12 min — covers single-serve + batch

export const BREW_POLL_UNTIL_KEY = "brew.pollUntil";

export interface BrewNowResult {
  ready_at?: string;
}

export async function brewNow(profileId: string, waterMl: number): Promise<BrewNowResult> {
  const result = await apiJson<BrewNowResult>("/schedules/brew-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_id: profileId, water_ml: waterMl }),
  });
  sessionStorage.setItem(BREW_POLL_UNTIL_KEY, String(Date.now() + POLL_WINDOW_MS));
  return result;
}
