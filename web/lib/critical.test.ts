import { describe, expect, it } from "vitest";
import { criticalSentence, thisYearSentence } from "./critical";
import { fmtRatio } from "./format";
import type { CriticalDoc } from "./types";

const base: CriticalDoc = { resolution: "month", baseline_years: [2003, 2021], excluded_years: [], min_years: 5, rule: "", threshold: 10, months: [10, 11, 12], onset: 10, peak: 11, end: 12, other_months: [], this_year: null };

describe("fmtRatio (2 significant figures)", () => {
  it("keeps small ratios readable: 0.05 is not 0.1", () => {
    expect(fmtRatio(0.05)).toBe("0.050");
    expect(fmtRatio(0.0537)).toBe("0.054");
    expect(fmtRatio(0.37)).toBe("0.37");
    expect(fmtRatio(1.744)).toBe("1.7");
    expect(fmtRatio(12.4)).toBe("12");
    expect(fmtRatio(130.2)).toBe("130");
    expect(fmtRatio(0)).toBe("0");
  });
});

describe("critical-period text", () => {
  it("names onset, peak and end", () => {
    expect(criticalSentence(base)).toContain("starts in October, peaks in November and ends in December");
  });
  it("does not repeat the month when the period is a single month", () => {
    const s = criticalSentence({ ...base, months: [5], onset: 5, peak: 5, end: 5 });
    expect(s).toContain("Typically confined to May");
    expect(s.match(/May/g)).toHaveLength(1);
  });
  it("keeps the second group of months for a single-month period", () => {
    const s = criticalSentence({ ...base, months: [5], onset: 5, peak: 5, end: 5, other_months: [9, 10] });
    expect(s).toContain("A second, smaller group of months: September, October.");
  });
  it("says so when no month qualifies", () => {
    expect(criticalSentence({ ...base, months: [], onset: null, peak: null, end: null })).toContain("No critical months");
  });
  it("this-year line states flag and critical status", () => {
    const t = thisYearSentence({ ...base, this_year: { month: "2025-11", value: 80, typical: 40, ratio: 2, in_critical: true, year_flagged: true } }, (m) => m);
    expect(t).toContain("2.0× the typical November");
    expect(t).toContain("is a critical month");
    expect(t).toContain("flagged");
  });
});
