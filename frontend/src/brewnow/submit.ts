import { apiFetch } from "../api/client";

const POLL_WINDOW_MS = 12 * 60 * 1000; // 12 min — covers single-serve + batch

export interface BrewNowResult {
  ready_at?: string;
}

export async function brewNow(profileId: string, waterMl: number): Promise<BrewNowResult> {
  const resp = await apiFetch("/schedules/brew-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_id: profileId, water_ml: waterMl }),
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`brew-now failed: ${resp.status} ${body}`);
  }
  sessionStorage.setItem("brew.pollUntil", String(Date.now() + POLL_WINDOW_MS));
  return (await resp.json()) as BrewNowResult;
}
