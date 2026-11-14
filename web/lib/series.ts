import { pointInGeometry, geometryBbox, bboxIntersects } from "./geo";
import { daysInMonth, monthRange, parseYm } from "./months";
import type { AreaDoc, CalibrationDoc, Platform, Series, Bbox } from "./types";

export type Mode = "harmonized" | "recorded" | Platform;


export const MODE_LABEL: Record<Mode, string> = {
  harmonized: "Harmonized (S-NPP scale)",
  recorded: "As recorded, unscaled",
  Terra: "Terra MODIS only",
  Aqua: "Aqua MODIS only",
  SNPP: "S-NPP VIIRS only",
  NOAA20: "NOAA-20 VIIRS only",
};

function median(xs: number[]): number | null {
  if (xs.length === 0) return null;
  const s = [...xs].sort((a, b) => a - b);
  const h = Math.floor(s.length / 2);
  const v = s.length % 2 ? s[h]! : (s[h - 1]! + s[h]!) / 2;
  return Math.round(v * 10) / 10;
}

export function monthlyMedian(months: string[], value: (number | null)[], partial: (boolean | null)[], years: [number, number]) {
  const buckets: number[][] = Array.from({ length: 12 }, () => []);
  months.forEach((k, i) => {
    const { y, m } = parseYm(k);
    const v = value[i];
    if (y < years[0] || y > years[1] || v === null || v === undefined || partial[i] !== false) return;
    buckets[m - 1]!.push(v);
  });
  return { values: buckets.map(median), n: buckets.map((b) => b.length) };
}

export function monthsOf(doc: { period: { first: string; last: string } }): string[] {
  return monthRange(doc.period.first, doc.period.last);
}

/** One displayed series from a precomputed area document (district or region). */
export function seriesFromDoc(doc: AreaDoc, mode: Mode): Series {
  const months = monthsOf(doc);
  if (mode === "harmonized") {
    const m = doc.median.harmonized;
    return {
      months, value: doc.harmonized.value, partial: doc.harmonized.partial, source: doc.harmonized.source,
      median: m.values, medianYears: m.baseline_years, medianN: m.n_years, unit: doc.units.harmonized, label: MODE_LABEL.harmonized,
    };
  }
  if (mode === "recorded") {
    // Each month shows the one platform that is its harmonized source, unscaled. Never a sum.
    const value = months.map((_, i) => {
      const src = doc.harmonized.source[i];
      return src ? (doc.raw[src as Platform]?.n[i] ?? null) : null;
    });
    const partial = months.map((_, i) => {
      const src = doc.harmonized.source[i];
      return src ? (doc.raw[src as Platform]?.partial[i] ?? null) : null;
    });
    return {
      months, value, partial, source: doc.harmonized.source, median: Array(12).fill(null), medianYears: null, medianN: Array(12).fill(0),
      unit: doc.units.raw, label: MODE_LABEL.recorded,
    };
  }
  const r = doc.raw[mode];
  const m = doc.median[mode];
  return {
    months, value: r.n, partial: r.partial, source: months.map(() => mode), median: m.values, medianYears: m.baseline_years,
    medianN: m.n_years, unit: doc.units.raw, label: MODE_LABEL[mode],
  };
}

export interface CustomInputs {
  months: string[];
  counts: Map<string, number>; // `${platform}|${ym}` -> n
  aquaPts: { lat: number; lon: number; ym: string }[];
  cal: CalibrationDoc;
  aoiBbox: Bbox;
  /** Baseline years per series, copied from a precomputed region doc so the rule matches. */
  baselines: Record<"harmonized" | Platform, [number, number]>;
  units: { harmonized: string; raw: string };
  /** constants.json partial_coverage (calibrate.PARTIAL_COVERAGE): complete month = share of days >= this. */
  partialCoverage: number;
}

export type CustomDoc = Omit<AreaDoc, "id" | "level" | "name" | "country" | "adm1" | "bbox" | "eras"> & { regionShare: Record<string, number> };

/**
 * Harmonized + raw series for a drawn box or radius, computed from tile detections with the
 * D-027 splice and per-detection calibration region (D-036). Platforms are never added.
 */
export function customDoc(inp: CustomInputs): CustomDoc {
  const { months, counts, cal } = inp;
  const avail = (p: string, ym: string) => cal.days_available[p]?.[ym] ?? 0;
  const raw = {} as AreaDoc["raw"];
  for (const p of ["Terra", "Aqua", "SNPP", "NOAA20"] as Platform[]) {
    raw[p] = {
      n: months.map((ym) => (avail(p, ym) > 0 ? (counts.get(`${p}|${ym}`) ?? 0) : null)),
      partial: months.map((ym) => (avail(p, ym) > 0 ? avail(p, ym) / daysInMonth(ym) < inp.partialCoverage : null)),
    };
  }
  // Region of each Aqua detection: PK Punjab polygon, else IN Punjab polygon, else rest_of_box.
  const polys = Object.entries(cal.punjab_polygons).filter(([, g]) => bboxIntersects(geometryBbox(g), inp.aoiBbox));
  const fac = cal.factors["Aqua->SNPP"] ?? {};
  // A null lo/hi bound makes that month's interval undefined (null), never the point factor (D-038).
  const perMonth = new Map<string, { v: number; lo: number | null; hi: number | null; undef: boolean }>();
  const regionCount: Record<string, number> = {};
  for (const pt of inp.aquaPts) {
    if (pt.ym >= cal.snpp_first) continue;
    const hit = polys.find(([, g]) => pointInGeometry(pt.lon, pt.lat, g));
    const region = hit ? hit[0] : "rest_of_box";
    regionCount[region] = (regionCount[region] ?? 0) + 1;
    const mi = parseYm(pt.ym).m - 1;
    const f = fac[region]?.factor[mi] ?? null;
    const acc = perMonth.get(pt.ym) ?? { v: 0, lo: 0, hi: 0, undef: false };
    if (f === null) acc.undef = true;
    else {
      acc.v += f;
      const l = fac[region]?.lo[mi] ?? null, h = fac[region]?.hi[mi] ?? null;
      acc.lo = acc.lo === null || l === null ? null : acc.lo + l;
      acc.hi = acc.hi === null || h === null ? null : acc.hi + h;
    }
    perMonth.set(pt.ym, acc);
  }
  const value: (number | null)[] = [], lo: (number | null)[] = [], hi: (number | null)[] = [];
  const source: (Platform | null)[] = [], partial: (boolean | null)[] = [];
  const r1 = (x: number) => Math.round(x * 10) / 10;
  for (const [i, ym] of months.entries()) {
    const src: Platform | null = ym < cal.snpp_first ? "Aqua" : ym <= cal.snpp_last ? "SNPP" : null;
    if (!src || avail(src, ym) === 0) {
      value.push(null); lo.push(null); hi.push(null); source.push(null); partial.push(null);
      continue;
    }
    source.push(src);
    partial.push(avail(src, ym) / daysInMonth(ym) < inp.partialCoverage);
    if (src === "SNPP") {
      const n = raw.SNPP.n[i] ?? 0;
      value.push(n); lo.push(n); hi.push(n);
    } else {
      const acc = perMonth.get(ym);
      if (!acc) { value.push(0); lo.push(0); hi.push(0); }
      else if (acc.undef) { value.push(null); lo.push(null); hi.push(null); }
      else { value.push(r1(acc.v)); lo.push(acc.lo === null ? null : r1(acc.lo)); hi.push(acc.hi === null ? null : r1(acc.hi)); }
    }
  }
  const mk = (v: (number | null)[], p: (boolean | null)[], years: [number, number]) => {
    const m = monthlyMedian(months, v, p, years);
    return { baseline_years: years, rule: "median over baseline years of complete months (>=90% days available)", values: m.values, n_years: m.n };
  };
  const median = {
    harmonized: mk(value, partial, inp.baselines.harmonized),
    Terra: mk(raw.Terra.n, raw.Terra.partial, inp.baselines.Terra),
    Aqua: mk(raw.Aqua.n, raw.Aqua.partial, inp.baselines.Aqua),
    SNPP: mk(raw.SNPP.n, raw.SNPP.partial, inp.baselines.SNPP),
    NOAA20: mk(raw.NOAA20.n, raw.NOAA20.partial, inp.baselines.NOAA20),
  };
  return {
    period: { first: months[0]!, last: months[months.length - 1]!, n_months: months.length },
    units: { ...inp.units, time: "local solar month" },
    harmonized: { value, lo, hi, source, partial },
    raw,
    median,
    regionShare: regionCount,
  };
}
