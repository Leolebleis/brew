import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import type { ReactElement } from "react";
import { BrewNowSheet } from "./sheet";

function wrap(node: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{node}</QueryClientProvider>;
}

const ACTIVE_BAG = {
  id: "b1",
  name: "Daybreak",
  remaining_grams: 312,
  is_active: true,
  profile_id: "p1",
  profile_snapshot: { target_volume: 250 },
};

describe("BrewNowSheet", () => {
  it("disables submit when lid is open", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.endsWith("/device")) return new Response(JSON.stringify({ brewing: false, lid_closed: false, basket_present: true, carafe_present: true }), { status: 200 });
      if (url.endsWith("/bags?active=true")) return new Response(JSON.stringify([ACTIVE_BAG]), { status: 200 });
      return new Response("{}", { status: 200 });
    }));
    render(wrap(<BrewNowSheet open={true} onClose={() => {}} />));
    // wait for queries to populate
    await screen.findByText(/Daybreak/);
    const buttons = screen.getAllByRole("button", { name: /brew now/i });
    // Last button is the submit (cancel doesn't match /brew now/)
    const btn = buttons[buttons.length - 1];
    expect(btn).toBeDisabled();
  });

  it("enables submit when all preflight fields are good", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.endsWith("/device")) return new Response(JSON.stringify({ brewing: false, lid_closed: true, basket_present: true, carafe_present: true }), { status: 200 });
      if (url.endsWith("/bags?active=true")) return new Response(JSON.stringify([ACTIVE_BAG]), { status: 200 });
      return new Response("{}", { status: 200 });
    }));
    render(wrap(<BrewNowSheet open={true} onClose={() => {}} />));
    await screen.findByText(/Daybreak/);
    const buttons = screen.getAllByRole("button", { name: /brew now/i });
    const btn = buttons[buttons.length - 1];
    expect(btn).not.toBeDisabled();
  });
});
