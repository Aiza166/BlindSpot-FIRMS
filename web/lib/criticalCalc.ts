// Critical period and median excluding flagged years, computed in the browser for drawn areas (D-043).
// Same definitions as the pipeline's appdata.critical_periods (D-042), which is the reference
// implementation; lib/criticalCalc.test.ts proves equality against tests/fixtures/critical_crosscheck.json.
import { monthlyMedian } from "./series";
import { parseYm } from "./months";
import type { CriticalDoc, MedianExclBlock } from "./types";

export const MIN_YEARS_CRITICAL = 5; // appdata.MIN_YEARS_CRITICAL

const r1 = (x: number) => Math.round(x * 10) / 10;
const r3 = (x: number) => Math.round(x * 1000) / 1000;

/** numpy.percentile, linear interpolation (same lerp formula as numpy >= 1.22). */
export function percentile(xs: number[], q: number): number {
  const s = [...xs].sort((a, b) => a - b);
  const pos = (s.length - 1) * (q / 100);
  const lo = Math.floor(pos), hi = Math.min(lo + 1, s.length - 1);
  const t = pos - lo, a = s[lo]!, b = s[hi]!;
  return t >= 0.5 ? b - (b - a) * (1 - t) : a + (b - a) * t;
}

/** Cyclic run of consecutive months (1-12) inside `months` that contains `peak`. */
function runAround(months: Set<number>, peak: number): number[] {
  const prev = (m: number) => ((m - 2 + 12) % 12) + 1, next = (m: number) => (m % 12) + 1;
  let start = peak;
  while (months.has(prev(start)) && prev(start) !== peak) start = prev(start);
  const run = [start];
  let cur = start;
  while (months.has(next(cur)) && next(cur) !== start) { cur = next(cur); run.push(cur); }
  return run;
}

export interface CriticalInput {
  /** "YYYY-MM" keys aligned with value and partial, first to last month of the record. */
  months: string[];
  value: (number | null)[];
  partial: (boolean | null)[];
  /** Baseline years of the area's all-years harmonized median (first data year to last full year). */
  baseline: [number, number];
  /** Caution years of the area (for a drawn area: the union over the overlapped regions, D-040). */
  cautionYears: number[];
}

export function computeCritical(inp: CriticalInput): { median_excl_flagged: MedianExclBlock; critical: CriticalDoc } {
  const [y0, y1] = inp.baseline;
  const excluded = [...new Set(inp.cautionYears.filter((y) => y >= y0 && y <= y1))].sort((a, b) => a - b);
  const dropped = new Set(excluded);
  const masked = inp.months.map((k, i) => (dropped.has(parseYm(k).y) ? null : (inp.value[i] ?? null)));
  const m = monthlyMedian(inp.months, masked, inp.partial, inp.baseline);
  const med: MedianExclBlock = {
    baseline_years: inp.baseline,
    rule: "median over baseline years of complete months, caution years left out",
    values: m.values,
    n_years: m.n,
    excluded_years: excluded,
  };
  const typ = new Map<number, number>();
  m.values.forEach((v, i) => { if (v !== null && m.n[i]! >= MIN_YEARS_CRITICAL) typ.set(i + 1, v); });
  const crit: CriticalDoc = {
    resolution: "month",
    baseline_years: inp.baseline,
    excluded_years: excluded,
    min_years: MIN_YEARS_CRITICAL,
    rule: "critical months = typical value at or above the 75th percentile of the twelve typical monthly values (excluding caution years), above zero",
    threshold: null, months: [], onset: null, peak: null, end: null, other_months: [], this_year: null,
  };
  if (typ.size) {
    const q75 = percentile([...typ.values()], 75);
    crit.threshold = r1(q75);
    const cm = new Set([...typ].filter(([, v]) => v >= q75 && v > 0).map(([k]) => k));
    if (cm.size) {
      const peak = [...cm].sort((a, b) => typ.get(b)! - typ.get(a)! || a - b)[0]!;
      const run = runAround(cm, peak);
      crit.months = [...cm].sort((a, b) => a - b);
      crit.onset = run[0]!; crit.peak = peak; crit.end = run[run.length - 1]!;
      crit.other_months = crit.months.filter((x) => !run.includes(x));
    }
  }
  const li = inp.months.length - 1;
  const last = inp.months[li];
  const v = inp.value[li] ?? null;
  if (last && v !== null && inp.partial[li] === false) {
    const { y, m: lm } = parseYm(last);
    const t = med.values[lm - 1] ?? null;
    crit.this_year = {
      month: last, value: r1(v), typical: t, ratio: t ? r3(v / t) : null,
      in_critical: crit.months.includes(lm), year_flagged: inp.cautionYears.includes(y),
    };
  }
  return { median_excl_flagged: med, critical: crit };
}
