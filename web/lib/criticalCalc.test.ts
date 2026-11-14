import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { computeCritical, percentile } from "./criticalCalc";

// Fixture written by tests/test_critical_crosscheck.py from the Python reference (appdata.critical_periods, D-042).
interface Case { name: string; months: string[]; value: (number | null)[]; partial: (boolean | null)[]; baseline: [number, number]; caution_years: number[]; expected: { median_excl_flagged: { values: (number | null)[]; n_years: number[]; excluded_years: number[]; baseline_years: number[] }; critical: Record<string, unknown> & { threshold: number | null; this_year: { typical: number | null; ratio: number | null; value: number | null } | null } } }
const fx = JSON.parse(readFileSync(new URL("../../tests/fixtures/critical_crosscheck.json", import.meta.url), "utf-8")) as { tolerance: number; cases: Case[] };

describe("computeCritical equals the Python reference (D-043)", () => {
  it("has two real districts and a synthetic case", () => {
    expect(fx.cases.map((c) => c.name)).toEqual(["Sangrur", "Kasur", "synthetic_wrap"]);
  });
  for (const c of fx.cases) {
    it(`${c.name}: months, onset/peak/end exact; typical values within ${fx.tolerance}`, () => {
      const got = computeCritical({ months: c.months, value: c.value, partial: c.partial, baseline: c.baseline, cautionYears: c.caution_years });
      const e = c.expected;
      expect(got.median_excl_flagged.n_years).toEqual(e.median_excl_flagged.n_years);
      expect(got.median_excl_flagged.excluded_years).toEqual(e.median_excl_flagged.excluded_years);
      got.median_excl_flagged.values.forEach((v, i) => {
        const w = e.median_excl_flagged.values[i] ?? null;
        if (v === null || w === null) expect(v).toBe(w);
        else expect(Math.abs(v - w)).toBeLessThanOrEqual(fx.tolerance + 1e-9);
      });
      for (const k of ["resolution", "min_years", "months", "onset", "peak", "end", "other_months", "excluded_years", "baseline_years"] as const) {
        expect(got.critical[k]).toEqual(e.critical[k]);
      }
      expect(Math.abs((got.critical.threshold ?? 0) - (e.critical.threshold ?? 0))).toBeLessThanOrEqual(fx.tolerance + 1e-9);
      const gt = got.critical.this_year, et = e.critical.this_year;
      expect(gt?.month).toEqual((et as unknown as { month: string }).month);
      expect(gt?.in_critical).toEqual((et as unknown as { in_critical: boolean }).in_critical);
      expect(gt?.year_flagged).toEqual((et as unknown as { year_flagged: boolean }).year_flagged);
      expect(gt?.value).toBe(et?.value);
      expect(Math.abs((gt?.ratio ?? 0) - (et?.ratio ?? 0))).toBeLessThan(0.01);
    });
  }
  it("percentile matches numpy linear interpolation", () => {
    expect(percentile([1, 2, 3, 4], 75)).toBeCloseTo(3.25, 12);
    expect(percentile([5], 75)).toBe(5);
  });
});
