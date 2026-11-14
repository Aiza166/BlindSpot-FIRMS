// Reliability flags (D-039, t3.json A7) as shown in the calendar. Codes come from the data;
// this module only turns them into plain words and merges flags for custom areas (D-040).
import { pointInGeometry } from "./geo";
import type { Aoi, Bbox } from "./types";

export interface Reliability {
  source: string;
  calib_region: string;
  inherited: boolean;
  years: string[];
  caution_years: Record<string, string[]>;
  reason_codes: Record<string, string>;
}

/** One flagged year: the reason codes and which calibration regions raised them. */
export interface FlagYear {
  year: number;
  reasons: { code: string; regions: string[] }[];
}

export interface Flags {
  years: Map<number, FlagYear>;
  /** Technical text per code, straight from the data (fallback for unknown codes). */
  codeText: Record<string, string>;
  /** Calibration regions whose flags apply (one for a district, one or more for a custom area). */
  regions: string[];
}

const PLAIN: Record<string, string> = {
  aqua_overpass_drift: "Aqua's afternoon pass drifted later, so the MODIS-to-VIIRS factor cannot be checked this year",
  burning_time_shift: "Some burning moved past the afternoon satellites, so the counts may understate it (a real decline is not ruled out)",
  pre2012_terra_aqua_trend: "Terra and Aqua MODIS drift apart before 2012, so the scaled MODIS counts may not be stable",
  splice_step_outside_normal: "The 2012 sensor switch leaves a larger step than the factor normally varies",
};

export const REGION_SHORT: Record<string, string> = { PK_Punjab: "Punjab (Pakistan)", IN_Punjab: "Punjab (India)", rest_of_box: "rest of the coverage box" };

/** Plain-language reason for a code; unknown codes fall back to the data's own text, then the code. */
export function plainReason(code: string, codeText: Record<string, string>): string {
  return PLAIN[code] ?? codeText[code] ?? code.replace(/_/g, " ");
}

/** Merge the reliability blocks of one or more calibration regions into per-year flags. */
export function mergeFlags(blocks: Reliability[]): Flags {
  const years = new Map<number, FlagYear>();
  const codeText: Record<string, string> = {};
  for (const b of blocks) {
    Object.assign(codeText, b.reason_codes);
    for (const [ys, codes] of Object.entries(b.caution_years)) {
      const y = Number(ys);
      const fy = years.get(y) ?? { year: y, reasons: [] };
      for (const code of codes) {
        const r = fy.reasons.find((x) => x.code === code);
        if (r) { if (!r.regions.includes(b.calib_region)) r.regions.push(b.calib_region); }
        else fy.reasons.push({ code, regions: [b.calib_region] });
      }
      years.set(y, fy);
    }
  }
  return { years, codeText, regions: blocks.map((b) => b.calib_region) };
}

/** Flagged years inside [from, to] ("YYYY-MM"), ascending. */
export function flaggedInRange(f: Flags | null, from: string, to: string): FlagYear[] {
  if (!f) return [];
  const y0 = Number(from.slice(0, 4)), y1 = Number(to.slice(0, 4));
  return [...f.years.values()].filter((fy) => fy.year >= y0 && fy.year <= y1).sort((a, b) => a.year - b.year);
}

/** Sentence for screen readers and the tooltip, e.g. "Caution year: Aqua's afternoon pass ...; Some burning ...". */
export function flagSentence(fy: FlagYear, f: Flags): string {
  const multi = f.regions.length > 1;
  return `Caution year: ${fy.reasons.map((r) => `${plainReason(r.code, f.codeText)}${multi ? ` (${r.regions.map((x) => REGION_SHORT[x] ?? x).join(", ")})` : ""}`).join("; ")}`;
}

/**
 * Calibration regions a custom area overlaps (D-040): a region counts if any point of a 21 x 21
 * grid over the area (inside the circle, for point + radius) falls in it. PK is tested before IN,
 * as in the custom splice (D-036); a point in neither belongs to rest_of_box.
 */
/** Keeps only regions with an index.json entry, so no file is fetched at an empty path. */
export function knownRegions(regs: string[], index: Record<string, string>): string[] {
  return regs.filter((r) => Object.hasOwn(index, r));
}

export function overlappedRegions(aoi: Aoi, bbox: Bbox, polygons: Record<string, GeoJSON.Geometry>): string[] {
  const hit = new Set<string>();
  const N = 21;
  const classify = (lon: number, lat: number) =>
    polygons.PK_Punjab && pointInGeometry(lon, lat, polygons.PK_Punjab) ? "PK_Punjab"
      : polygons.IN_Punjab && pointInGeometry(lon, lat, polygons.IN_Punjab) ? "IN_Punjab" : "rest_of_box";
  if (aoi.kind === "radius") hit.add(classify(aoi.lon, aoi.lat));
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < N; j++) {
      const lon = bbox[0] + ((bbox[2] - bbox[0]) * i) / (N - 1);
      const lat = bbox[1] + ((bbox[3] - bbox[1]) * j) / (N - 1);
      if (aoi.kind === "radius") {
        const dx = (lon - aoi.lon) * 111.32 * Math.cos((aoi.lat * Math.PI) / 180), dy = (lat - aoi.lat) * 110.57;
        if (Math.hypot(dx, dy) > aoi.km) continue;
      }
      hit.add(classify(lon, lat));
    }
  }
  return ["PK_Punjab", "IN_Punjab", "rest_of_box"].filter((r) => hit.has(r));
}
