// Typed views of results/t1.json, t2.json, charts_t2.json, mask_report.json (only fields we render).

export interface Step2012 {
  raw_step: number;
  harmonized_step: number;
  ratio: number;
  ratio_ci95: [number, number];
  threshold: number;
  pass: boolean;
  aqua_window_total: number;
  snpp_window_total: number;
}

export interface T1 {
  window: { start: string; end: string; time_basis: string };
  parameters: { step_year: number; calib_years: number[]; heldout_years: number[]; step_threshold: number; pi_level: number; bootstrap_b: number };
  results: { hotspots: Record<string, { step_2012: Step2012; heldout: { n: number; n_inside: number; pass: boolean } }> };
}

export interface PiTest { pi_ratio: [number, number]; test_mean_ratio: number; test_vs_base_pct: number; outside: boolean }
export interface TheilSen { slope_pct_per_year: number; ci95_pct_per_year: [number, number]; excludes_zero: boolean }

export interface T2Region {
  evaluable_test_years: Record<string, { evaluable: boolean; matched_days: number; reason: string }>;
  verdict: { label: string; rule: string };
  verdict_revised: { label: string; evaluable_test_years: number[]; pi_test: PiTest | null; theil_sen: TheilSen | null };
  aqua_drift_effect: { effect_pct_per_hour: number; effect_ci95_pct_per_hour: [number, number]; slope_p: number };
  min_detectable_drift: { pct: number };
}

export interface YearShare { night: number; day: number; share: number; n_days: number }

export interface T2 {
  control_note: string;
  parameters: { match_tolerance_h: number; calib_years: number[]; test_years: number[] };
  t2: Record<string, T2Region>;
  t2b: Record<string, { night_share: Record<string, Record<string, YearShare>> }>;
  t1_reevaluated: Record<string, { label: string; basis: string; status: string; pass: boolean }>;
}

export interface ChartsT2 {
  note: string;
  overpass_by_year: Record<string, Record<string, Record<string, { median_h: number; n_days: number }>>>;
  ratio_vs_delta: Record<string, { date: string; delta_h: number; ratio: number }[]>;
}

export interface MaskReport {
  n_masked_cells: number;
  detections_total_by_platform: Record<string, number>;
  detections_removed_by_platform: Record<string, number>;
  share_removed_by_platform: Record<string, number>;
  parameters: { rule: string; grid_deg: number; min_years: number };
}

export function verdictClass(label: string): "pass" | "fail" | "inconclusive" {
  const l = label.toLowerCase();
  if (l.startsWith("inconclusive")) return "inconclusive";
  if (l.startsWith("fail") || l.startsWith("drift")) return "fail";
  return "pass";
}

export const REGION_NAME: Record<string, string> = {
  PK_Punjab: "Punjab, Pakistan",
  IN_Punjab: "Punjab, India",
  rest_of_box: "Rest of the coverage box (control)",
};

export function meanShare(byYear: Record<string, YearShare>, years: number[]): number | null {
  const xs = years.map((y) => byYear[String(y)]?.share).filter((v): v is number => typeof v === "number");
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
}

export function maxShare(byYear: Record<string, YearShare>, years: number[]): number | null {
  const xs = years.map((y) => byYear[String(y)]?.share).filter((v): v is number => typeof v === "number");
  return xs.length ? Math.max(...xs) : null;
}

// t3.json (D-039): only the fields the Results page renders.
export interface T3Evidence { supporting: string[]; against: string[]; verdict: string }
export interface DayNight { night: number; day: number; share: number; n_days: number }
export interface T3Region {
  a1_noaa20_snpp: { by_year: Record<string, { noaa20: number; snpp: number; ratio: number; n_days: number }>; theil_sen: TheilSen; stable: boolean };
  a2_viirs_only: { snpp: Record<string, DayNight>; noaa20: Record<string, DayNight> };
  evidence: Record<"O" | "T" | "D", T3Evidence>;
  reliability: Record<string, { harmonization_reliable: string; reasons: string[] }>;
}
export interface T3 {
  regions: string[];
  control_region: string;
  window: { start: string; end: string; time_basis: string };
  parameters: { pre_years: number[]; post_years: number[] };
  reason_codes: Record<string, string>;
  district_inheritance: string;
  t3: Record<string, T3Region>;
}

export const EXPLANATION: Record<"O" | "T" | "D", string> = {
  O: "O: Aqua orbit drift",
  T: "T: burning later in the day",
  D: "D: real decline",
};

/** Explanation verdicts are not pass/fail; map them onto the three existing verdict styles. */
export function t3VerdictClass(v: string): "pass" | "fail" | "inconclusive" {
  if (v === "supported") return "pass";
  if (v === "not supported") return "fail";
  return "inconclusive";
}
