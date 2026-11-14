import { describe, expect, it } from "vitest";
import { landing, storyFromT1, STORY_REGION } from "./story";
import type { T1 } from "./results";

const step = (raw: number, harm: number) => ({ step_2012: { raw_step: raw, harmonized_step: harm, ratio: 0, ratio_ci95: [0, 0] as [number, number], threshold: 0.1, pass: true, aqua_window_total: 0, snpp_window_total: 0 }, heldout: { n: 4, n_inside: 4, pass: true } });
const t1 = {
  window: { start: "10-15", end: "11-30", time_basis: "local solar date" },
  parameters: { step_year: 2012, calib_years: [], heldout_years: [], step_threshold: 0.1, pi_level: 0.95, bootstrap_b: 1 },
  results: { hotspots: { PK_Punjab: step(6.131168831168831, 0.12668484182590878), IN_Punjab: step(3.709, -0.0609) } },
} as T1;

const index = { regions: { PK_Punjab: "regions/pk_punjab.json", IN_Punjab: "regions/in_punjab.json" }, districts: [{ id: "D1", name: "Amritsar" }, { id: "D2", name: "Lahore" }] };

describe("2012 story text", () => {
  it("formats the steps and the window from t1.json, with no number of its own", () => {
    expect(storyFromT1(t1)).toEqual({ region: STORY_REGION, year: 2012, window: "15 October to 30 November", raw: "+613%", harmonized: "+12.7%" });
  });
  it("keeps the sign of a negative harmonized step", () => {
    expect(storyFromT1(t1, "IN_Punjab")?.harmonized).toBe("-6.1%");
  });
  it("returns null when the region has no step result", () => {
    expect(storyFromT1(t1, "rest_of_box")).toBeNull();
  });
});

describe("landing area", () => {
  it("opens on the story region when there is no deep link", () => {
    expect(landing(index, null)).toEqual({ id: STORY_REGION, story: true });
  });
  it("a deep link to a district wins and turns the story off", () => {
    expect(landing(index, "D2")).toEqual({ id: "D2", story: false });
  });
  it("an unknown deep link falls back to the story", () => {
    expect(landing(index, "nope")).toEqual({ id: STORY_REGION, story: true });
  });
  it("without the story region it falls back to Amritsar, then the first district", () => {
    expect(landing({ regions: {}, districts: index.districts }, null)).toEqual({ id: "D1", story: false });
    expect(landing({ regions: {}, districts: [{ id: "D2", name: "Lahore" }] }, null)).toEqual({ id: "D2", story: false });
    expect(landing({ regions: {}, districts: [] }, null)).toBeNull();
  });
});
