import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { RatingToast } from "./toast";
import { ToastProvider } from "../components/toast";

describe("RatingToast", () => {
  it("PATCHes /journal/{id} on star tap", async () => {
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      void _url;
      if (init?.method === "PATCH") return new Response("{}", { status: 200 });
      return new Response("{}", { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const onClose = vi.fn();
    render(
      <ToastProvider>
        <RatingToast entryId="e1" open={true} onClose={onClose} />
      </ToastProvider>
    );
    const stars = screen.getAllByRole("button", { name: /rate/i });
    await userEvent.click(stars[3]); // 4 stars

    expect(fetchMock).toHaveBeenCalled();
    const patchCall = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === "PATCH");
    expect(patchCall).toBeDefined();
    expect(String(patchCall![0])).toContain("/journal/e1");
    expect(JSON.parse((patchCall![1] as RequestInit).body as string)).toEqual({ rating: 4 });
  });
});
