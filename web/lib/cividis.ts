// Cividis ramp (Nuñez, Anderton & Renslow 2018), 9 stops sampled from matplotlib's table.
const STOPS: [number, number, number][] = [
  [0, 34, 78], [18, 53, 112], [59, 73, 108], [87, 92, 109], [112, 113, 115],
  [138, 134, 120], [166, 157, 117], [196, 181, 106], [254, 232, 56],
];

export function cividis(t: number): string {
  const x = Math.min(1, Math.max(0, t)) * (STOPS.length - 1);
  const i = Math.min(STOPS.length - 2, Math.floor(x));
  const f = x - i;
  const a = STOPS[i]!;
  const b = STOPS[i + 1]!;
  const c = a.map((v, k) => Math.round(v + (b[k]! - v) * f));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

/** Relative luminance check so the in-cell value text stays readable. */
export function textOn(t: number): string {
  return t > 0.55 ? "#10161f" : "#f4f6f8";
}

/** Square-root scale: burning counts are heavy-tailed; sqrt keeps small months visible. */
export function scaleT(v: number, max: number): number {
  if (max <= 0) return 0;
  return Math.sqrt(Math.max(0, v) / max);
}
