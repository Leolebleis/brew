import { useQuery, type QueryClient } from "@tanstack/react-query";
import { apiJson } from "../api/client";
import { StatusEvent } from "./events";

export interface DeviceState {
  brewing: boolean;
  brew_started_at?: string;
  brew_end_time?: string;
  lid_closed?: boolean;
  basket_present?: boolean;
  carafe_present?: boolean;
  [k: string]: unknown;
}

export interface Bag {
  id: string;
  name: string;
  remaining_grams: number;
  profile_id: string | null;
  profile_snapshot: Record<string, unknown>;
  is_active: boolean;
}

export interface WaterState {
  remaining_ml: number;
  last_refilled_at: string | null;
}

export function useDevice(opts?: { refetchIntervalMs?: number | false }) {
  return useQuery({
    queryKey: ["device"],
    queryFn: () => apiJson<DeviceState>("/device"),
    refetchInterval: opts?.refetchIntervalMs ?? false,
  });
}

export function useActiveBag() {
  return useQuery({
    queryKey: ["bags", "active"],
    queryFn: async () => {
      const list = await apiJson<Bag[]>("/bags?active=true");
      return list[0] ?? null;
    },
  });
}

export function useWater() {
  return useQuery({
    queryKey: ["water"],
    queryFn: () => apiJson<WaterState>("/water"),
  });
}

export function handleStatusEvent(qc: QueryClient, name: string, data: unknown): void {
  void data;
  switch (name) {
    case StatusEvent.BrewCompleted:
      qc.invalidateQueries({ queryKey: ["device"] });
      return;
    case StatusEvent.BagActivated:
    case StatusEvent.BagFinished:
      // ["bags"] is a prefix match — covers ["bags", "active"] automatically.
      qc.invalidateQueries({ queryKey: ["bags"] });
      return;
    case StatusEvent.WaterRefilled:
      qc.invalidateQueries({ queryKey: ["water"] });
      return;
    default:
      return;
  }
}
