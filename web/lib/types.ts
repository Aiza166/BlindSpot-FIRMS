import type { Reliability } from "./reliability";

// Shapes of the static data written by pipeline/blindspot/appdata.py (D-035, D-036).

export const PLATFORMS = ["Terra", "Aqua", "SNPP", "NOAA20"] as const;
export type Platform = (typeof PLATFORMS)[number];

export type Bbox = [number, number, number, number]; // lon_min, lat_min, lon_max, lat_max

export interface Constants {
  schema_version: number;
  csv_row_cap: number;
  csv_cap_message: string;
  tile_deg: number;
  tile_path_template: string;
  coverage_box: { lon_min: number; lon_max: number; lat_min: number; lat_max: number };
  platforms: Platform[];
  units: { harmonized: string; raw: string };
  nrt_label: string;
  scope: string;
  partial_coverage: number;
  /** First month (YYYY-MM) of near-real-time data per platform (decisions.md W-12); absent before 2026 data. */
  provisional_from?: Partial<Record<Platform, string>>;
}

export interface DistrictEntry {
  id: string;
  name: string;
  country: "PAK" | "IND" | string;
  bbox: Bbox;
  adm1: string;
}

export interface IndexDoc {
  schema_version: number;
  period: { first: string; last: string };
  boundaries: string;
  regions: Record<string, string>;
  districts: DistrictEntry[];
}

export interface Era {
  start: string;
  end: string | null;
  label: string;
  source: Platform;
  in_series: boolean;
  note?: string;
}

export interface MedianBlock {
  baseline_years: [number, number];
  rule: string;
  values: (number | null)[];
  n_years: number[];
}

/** Median with the area's caution years left out (D-042). */
export interface MedianExclBlock extends MedianBlock {
  excluded_years: number[];
}

/** Month-level critical periods (D-042). Months are 1-12. */
export interface CriticalDoc {
  resolution: "month";
  baseline_years: [number, number];
  excluded_years: number[];
  min_years: number;
  rule: string;
  threshold: number | null;
  months: number[];
  onset: number | null;
  peak: number | null;
  end: number | null;
  other_months: number[];
  this_year: {
    month: string;
    value: number | null;
    typical: number | null;
    ratio: number | null;
    in_critical: boolean;
    year_flagged: boolean;
  } | null;
}

export interface AreaDoc {
  id: string;
  level: string;
  name: string;
  country: string;
  adm1: { id: string; name: string };
  bbox: Bbox;
  period: { first: string; last: string; n_months: number };
  units: { harmonized: string; raw: string; time: string };
  eras: Era[];
  harmonized: {
    value: (number | null)[];
    lo: (number | null)[];
    hi: (number | null)[];
    source: (Platform | null)[];
    partial: (boolean | null)[];
    /** Near-real-time months (rule 8: shown as provisional); absent in older data. */
    provisional?: boolean[];
  };
  raw: Record<Platform, { n: (number | null)[]; partial: (boolean | null)[]; provisional?: boolean[] }>;
  median: Record<"harmonized" | Platform, MedianBlock>;
  /** Harmonized median without the caution years (D-042); absent in older data. */
  median_excl_flagged?: MedianExclBlock;
  critical?: CriticalDoc;
  /** Reliability flags of the calibration region (D-039); absent in older data. */
  reliability?: Reliability;
}

export interface CalibrationDoc {
  unit: string;
  rule: string;
  snpp_first: string;
  snpp_last: string;
  factors: Record<string, Record<string, { factor: (number | null)[]; lo: (number | null)[]; hi: (number | null)[] }>>;
  punjab_polygons: Record<string, GeoJSON.Geometry>;
  polygon_simplify_tolerance_deg: number;
  days_available: Record<string, Record<string, number>>;
  provisional_from?: Partial<Record<Platform, string>>;
}

export interface TileManifest {
  tile_deg: number;
  path_template: string;
  columns: string[];
  csv_row_cap: number;
  rows: Record<string, Record<string, number>>;
}

/** The area the user chose. Districts carry precomputed series; custom shapes are computed from tiles. */
export type Aoi =
  | { kind: "district"; id: string; name: string; bbox: Bbox; country: string }
  | { kind: "box"; bbox: Bbox }
  | { kind: "radius"; lat: number; lon: number; km: number };

/** One calendar series: 'months' are "YYYY-MM" keys aligned with values. */
export interface Series {
  months: string[];
  value: (number | null)[];
  partial: (boolean | null)[];
  /** Near-real-time months, shown as provisional (rule 8). */
  provisional?: boolean[];
  source: (string | null)[];
  median: (number | null)[]; // 12 calendar months
  medianYears: [number, number] | null;
  medianN: number[];
  unit: string;
  label: string;
}
