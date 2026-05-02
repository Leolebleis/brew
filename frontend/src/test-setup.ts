import { vi } from "vitest";
import "@testing-library/jest-dom/vitest";

vi.stubEnv("VITE_FELLOW_API_KEY", "test-key");

// JSDOM doesn't implement Pointer Capture; Radix Toast/Dialog use it.
if (typeof Element !== "undefined" && !Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
  Element.prototype.setPointerCapture = () => {};
  Element.prototype.releasePointerCapture = () => {};
}

// JSDOM lacks matchMedia; xterm.js queries it for theme/preference detection.
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList;
}
