import { describe, expect, it } from "vitest";
import { cardFootNote, showLaunchNote } from "./cardNote";
import type { NrtMonth } from "./nrt";

const ok = { status: "ok" as const, data: { label: "near-real-time, provisional", source: "VIIRS_NOAA20_NRT" } as NrtMonth };
const failed = { status: "unavailable" as const, reason: "FIRMS did not answer in time" };
const noBuild = { status: "unavailable" as const, reason: "No near-real-time service in this build." };

describe("month card foot note (FIXES_FOR_KISSA item 2)", () => {
  it("while the live request runs on a build with the service, says it is loading", () => {
    expect(cardFootNote(null, true)).toBe("Loading the live current month…");
  });
  it("a build without the service says so, before and after the (skipped) request", () => {
    for (const n of [null, noBuild]) expect(cardFootNote(n, false)).toContain("The live near-real-time service is not part of this build");
  });
  it("a failed request names the reason and the fallback", () => {
    expect(cardFootNote(failed, true)).toBe("Near-real-time data could not be loaded (FIRMS did not answer in time), so this card shows the latest month in the saved data.");
  });
  it("a loaded live month describes the live figure", () => {
    expect(cardFootNote(ok, true)).toContain("The near-real-time, provisional figure is FIRMS VIIRS_NOAA20_NRT");
  });
  it("the 'switched on at launch' note appears only on a build without the service", () => {
    expect(showLaunchNote(true)).toBe(false);
    expect(showLaunchNote(false)).toBe(true);
  });
});
