import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import type { ReactElement } from "react";
import { StatusHeader } from "./header";

function wrap(node: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{node}</QueryClientProvider>;
}

describe("StatusHeader", () => {
  it("renders 'Idle' when device not brewing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.endsWith("/device"))
          return new Response(JSON.stringify({ brewing: false }), { status: 200 });
        if (url.endsWith("/water"))
          return new Response(JSON.stringify({ remaining_ml: 1080 }), { status: 200 });
        if (url.endsWith("/bags?active=true"))
          return new Response(
            JSON.stringify([
              {
                id: "b1",
                name: "Daybreak",
                remaining_grams: 312,
                is_active: true,
                profile_id: "p1",
                profile_snapshot: {},
              },
            ]),
            { status: 200 },
          );
        return new Response("{}", { status: 200 });
      }),
    );
    render(wrap(<StatusHeader onBrew={() => {}} />));
    expect(await screen.findByText(/idle/i)).toBeInTheDocument();
  });
});
