export const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api";
export const API_KEY = (import.meta.env.VITE_FELLOW_API_KEY as string | undefined) ?? "";

if (import.meta.env.PROD && !API_KEY) {
  console.error("VITE_FELLOW_API_KEY missing in production build — API calls will be unauthenticated");
}
