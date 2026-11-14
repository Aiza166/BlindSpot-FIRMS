const nf0 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });

/** Counts: integer when whole, else one decimal (harmonized values are scaled, so fractional). */
export function fmtCount(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "no data";
  return Number.isInteger(v) ? nf0.format(v) : nf1.format(v);
}

export function fmtPct(v: number, digits = 0, signed = false): string {
  const s = (v * 100).toFixed(digits);
  return `${signed && v > 0 ? "+" : ""}${s}%`;
}

export function fmtNum(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function fmtHour(h: number): string {
  const hh = Math.floor(h);
  const mm = Math.round((h - hh) * 60);
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}

/** Ratio to a median at 2 significant figures (0.050, 0.37, 1.7, 12); 10 and above are whole numbers. */
export function fmtRatio(r: number): string {
  if (!Number.isFinite(r)) return "n/a";
  if (r >= 10) return String(Math.round(r));
  return r === 0 ? "0" : r.toPrecision(2);
}
