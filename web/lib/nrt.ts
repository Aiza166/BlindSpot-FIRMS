// Near-real-time client (PLAN §6, D-010, D-040). The FIRMS MAP_KEY lives only in the server
// function's environment (functions/api/nrt.ts); this module never reads or holds a key.
// NEXT_PUBLIC_NRT_ENDPOINT is a URL only (e.g. "/api/nrt"); unset = cached snapshot.
import type { Bbox } from "./types";

/** Body of a successful GET /api/nrt (mirrors functions/_lib/nrt-core.ts NrtBody). */
export interface NrtMonth {
  status: "ok";
  provisional: true;
  /** constants.json nrt_label ("near-real-time, provisional"). */
  label: string;
  source: string;
  month: string;
  noaa20: number;
  masked: number;
  daysCovered: number;
  daysInMonth: number;
  median: { value: number | null; years: [number, number] } | null;
  geometry: "polygon" | "bbox";
  fetchedAt: string;
}

export type NrtResult =
  | { status: "ok"; data: NrtMonth }
  | { status: "unavailable"; reason: string };

export type NrtFetcher = (aoi: Bbox, area: string | null, signal?: AbortSignal) => Promise<NrtResult>;

export const NRT_ENDPOINT: string | null = process.env.NEXT_PUBLIC_NRT_ENDPOINT || null;

function isNrtMonth(x: unknown): x is NrtMonth {
  const o = x as Partial<NrtMonth> | null;
  return !!o && o.status === "ok" && o.provisional === true && typeof o.noaa20 === "number" && typeof o.month === "string";
}

/** True when month is the current or previous UTC month, the only months NRT serves. */
export function nrtMonthAllowed(month: string, now: Date = new Date()): boolean {
  const ym = (t: number) => new Date(t).toISOString().slice(0, 7);
  return month === ym(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)) || month === ym(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1));
}

/** Bbox query value rounded outward to 4 decimals, so rounding never shrinks the area. */
export function bboxParam([w, s, e, n]: Bbox): string {
  const dn = (v: number) => (Math.floor(v * 1e4 + 1e-6) / 1e4).toFixed(4), up = (v: number) => (Math.ceil(v * 1e4 - 1e-6) / 1e4).toFixed(4);
  return [dn(w), dn(s), up(e), up(n)].join(",");
}

export const fetchNrt: NrtFetcher = async (aoi, area, signal) => {
  if (!NRT_ENDPOINT) return { status: "unavailable", reason: "No near-real-time service in this build." };
  const q = new URLSearchParams({ bbox: bboxParam(aoi) });
  if (area) q.set("area", area);
  try {
    const r = await fetch(`${NRT_ENDPOINT}?${q.toString()}`, { signal });
    const body: unknown = await r.json().catch(() => null);
    if (!r.ok || !isNrtMonth(body)) {
      const reason = (body as { reason?: unknown } | null)?.reason;
      return { status: "unavailable", reason: typeof reason === "string" ? reason : `NRT service answered HTTP ${r.status}.` };
    }
    // Never label a month outside the NRT window as a near-real-time count.
    if (!nrtMonthAllowed(body.month)) return { status: "unavailable", reason: "The near-real-time service answered for a month outside its window." };
    return { status: "ok", data: body };
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    return { status: "unavailable", reason: "The near-real-time service could not be reached." };
  }
};
