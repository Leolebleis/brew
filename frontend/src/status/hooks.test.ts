import { describe, it, expect, vi } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { handleStatusEvent } from "./hooks";

describe("handleStatusEvent", () => {
  it("BrewCompleted invalidates device", () => {
    const qc = new QueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    handleStatusEvent(qc, "BrewCompleted", {});
    expect(spy).toHaveBeenCalledWith({ queryKey: ["device"] });
  });

  it("BagActivated invalidates bags + active bag", () => {
    const qc = new QueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    handleStatusEvent(qc, "BagActivated", { bag_id: "b1" });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["bags"] });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["bags", "active"] });
  });

  it("WaterRefilled invalidates water", () => {
    const qc = new QueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    handleStatusEvent(qc, "WaterRefilled", { remaining_ml: 1500 });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["water"] });
  });

  it("BagFinished invalidates bags + active bag", () => {
    const qc = new QueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    handleStatusEvent(qc, "BagFinished", { bag_id: "b1" });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["bags"] });
    expect(spy).toHaveBeenCalledWith({ queryKey: ["bags", "active"] });
  });

  it("unknown event is a no-op", () => {
    const qc = new QueryClient();
    const spy = vi.spyOn(qc, "invalidateQueries");
    handleStatusEvent(qc, "WhoKnows", {});
    expect(spy).not.toHaveBeenCalled();
  });
});
