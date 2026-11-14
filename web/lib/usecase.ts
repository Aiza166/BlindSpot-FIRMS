// Numbers for the use-case page (one district, one month), all read from the district JSON.
import { mergeFlags, plainReason, type FlagYear } from "./reliability";
import { monthsOf } from "./series";
import type { AreaDoc } from "./types";

export interface MonthCheck {
  ym: string;
  value: number | null;
  partial: boolean;
  source: string | null;
  median: number | null;
  medianYears: [number, number];
  medianN: number;
  /** Median without the district's caution years (D-042) and the years left out. */
  medianExcl: number | null;
  excludedYears: number[];
  /** Same calendar month of every complete year before ym, with values. */
  earlier: { year: number; value: number }[];
  minEarlier: { year: number; value: number } | null;
  maxEarlier: { year: number; value: number } | null;
  /** 1 = lowest among the same months up to and including ym. */
  rankFromLowest: number | null;
  nCompared: number;
  noaa20: number | null;
  noaa20Median: number | null;
  noaa20Years: [number, number];
  flag: FlagYear | null;
  flagText: string[];
}

export function checkMonth(doc: AreaDoc, ym: string): MonthCheck {
  const months = monthsOf(doc);
  const i = months.indexOf(ym);
  const m = Number(ym.slice(5, 7));
  const y = Number(ym.slice(0, 4));
  const val = (k: number) => (k >= 0 ? (doc.harmonized.value[k] ?? null) : null);
  const earlier: { year: number; value: number }[] = [];
  months.forEach((mm, k) => {
    const yy = Number(mm.slice(0, 4));
    if (Number(mm.slice(5, 7)) === m && yy < y && doc.harmonized.partial[k] !== true) {
      const v = val(k);
      if (v !== null) earlier.push({ year: yy, value: v });
    }
  });
  const v = val(i);
  const sorted = [...earlier].sort((a, b) => a.value - b.value);
  const all = v === null ? [] : [...earlier.map((e) => e.value), v].sort((a, b) => a - b);
  const flags = doc.reliability ? mergeFlags([doc.reliability]) : null;
  const flag = flags?.years.get(y) ?? null;
  return {
    ym,
    value: v,
    partial: i >= 0 && doc.harmonized.partial[i] === true,
    source: i >= 0 ? (doc.harmonized.source[i] ?? null) : null,
    median: doc.median.harmonized.values[m - 1] ?? null,
    medianYears: doc.median.harmonized.baseline_years,
    medianN: doc.median.harmonized.n_years[m - 1] ?? 0,
    medianExcl: doc.median_excl_flagged?.values[m - 1] ?? null,
    excludedYears: doc.median_excl_flagged?.excluded_years ?? [],
    earlier,
    minEarlier: sorted[0] ?? null,
    maxEarlier: sorted[sorted.length - 1] ?? null,
    rankFromLowest: v === null ? null : all.indexOf(v) + 1,
    nCompared: all.length,
    noaa20: i >= 0 ? (doc.raw.NOAA20.n[i] ?? null) : null,
    noaa20Median: doc.median.NOAA20.values[m - 1] ?? null,
    noaa20Years: doc.median.NOAA20.baseline_years,
    flag,
    flagText: flag && flags ? flag.reasons.map((r) => plainReason(r.code, flags.codeText)) : [],
  };
}

/**
 * D-042 flagship rule: the calendar month (default November) since `fromYear` with the highest
 * complete harmonized value among years that are not caution years for this district.
 * Ties go to the later year. Mirrors blindspot.story.flagship_month.
 */
export function flagshipMonth(doc: AreaDoc, calMonth = 11, fromYear = 2012): { ym: string; nEligible: number } | null {
  const caution = new Set(Object.keys(doc.reliability?.caution_years ?? {}).map(Number));
  let best: { ym: string; v: number; y: number } | null = null;
  let n = 0;
  monthsOf(doc).forEach((ym, k) => {
    const y = Number(ym.slice(0, 4)), v = doc.harmonized.value[k];
    if (Number(ym.slice(5, 7)) !== calMonth || y < fromYear || caution.has(y) || doc.harmonized.partial[k] !== false || v === null || v === undefined) return;
    n += 1;
    if (!best || v >= best.v) best = { ym, v, y };
  });
  const b = best as { ym: string } | null;
  return b ? { ym: b.ym, nEligible: n } : null;
}
