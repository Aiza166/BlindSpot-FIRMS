import type { ChartsT2, T3Region } from "@/lib/results";
import { fmtHour } from "@/lib/format";

const W = 640, H = 300, M = { l: 52, r: 100, t: 14, b: 36 };
const DASH: Record<string, string> = { Aqua: "", Terra: "6 4", SNPP: "2 3", NOAA20: "10 3 2 3" };
const NAME: Record<string, string> = { Aqua: "Aqua MODIS", Terra: "Terra MODIS", SNPP: "S-NPP VIIRS", NOAA20: "NOAA-20 VIIRS" };

function niceTicks(lo: number, hi: number, n = 5): number[] {
  const step = (hi - lo) / n;
  const p = Math.pow(10, Math.floor(Math.log10(step)));
  const s = [1, 2, 5, 10].map((k) => k * p).find((k) => k >= step) ?? step;
  const out: number[] = [];
  for (let v = Math.ceil(lo / s) * s; v <= hi + 1e-9; v += s) out.push(Number(v.toFixed(6)));
  return out;
}

/** Overpass time by year for each platform (charts_t2.overpass_by_year). Lines differ by dash and direct label. */
export function OverpassChart({ data, region, title, windowLabel }: { data: ChartsT2; region: string; title: string; windowLabel: string }) {
  const byP = data.overpass_by_year[region] ?? {};
  const pts = Object.entries(byP).flatMap(([p, ys]) => Object.entries(ys).map(([y, v]) => ({ p, y: Number(y), h: v.median_h })));
  if (pts.length === 0) return null;
  const x0 = Math.min(...pts.map((d) => d.y)), x1 = Math.max(...pts.map((d) => d.y));
  const y0 = Math.floor(Math.min(...pts.map((d) => d.h)) * 2) / 2, y1 = Math.ceil(Math.max(...pts.map((d) => d.h)) * 2) / 2;
  const sx = (x: number) => M.l + ((x - x0) / (x1 - x0)) * (W - M.l - M.r);
  const sy = (y: number) => H - M.b - ((y - y0) / (y1 - y0)) * (H - M.t - M.b);
  return (
    <figure className="chart" data-testid={`chart-overpass-${region}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${title}: median local solar time of daytime detections by year, per platform`}>
        {niceTicks(y0, y1).map((t) => (
          <g key={t}>
            <line x1={M.l} x2={W - M.r} y1={sy(t)} y2={sy(t)} stroke="var(--rule)" />
            <text x={M.l - 6} y={sy(t) + 4} textAnchor="end" fontSize="11" fill="var(--ink-2)">{fmtHour(t)}</text>
          </g>
        ))}
        {niceTicks(x0, x1, 6).map((t) => (
          <text key={t} x={sx(t)} y={H - M.b + 18} textAnchor="middle" fontSize="11" fill="var(--ink-2)">{t}</text>
        ))}
        {(() => {
          // End labels: keep at least 13 px apart so near-identical lines stay readable.
          const ends = Object.entries(byP).map(([p, ys]) => { const k = Object.keys(ys).map(Number).sort((a, b) => b - a)[0]!; return { p, y: sy(ys[String(k)]!.median_h) }; }).sort((a, b) => a.y - b.y);
          for (let k = 1; k < ends.length; k++) ends[k]!.y = Math.max(ends[k]!.y, ends[k - 1]!.y + 13);
          return ends.map((e) => <text key={e.p} x={W - M.r + 6} y={e.y + 4} fontSize="11.5" fill="var(--ink)">{NAME[e.p]}</text>);
        })()}
        {Object.entries(byP).map(([p, ys]) => {
          const s = Object.entries(ys).map(([y, v]) => [Number(y), v.median_h] as const).sort((a, b) => a[0] - b[0]);
          return (
            <g key={p}>
              <polyline fill="none" stroke="var(--ink)" strokeWidth={p === "Aqua" ? 2.2 : 1.4} strokeDasharray={DASH[p]} points={s.map(([x, y]) => `${sx(x)},${sy(y)}`).join(" ")} />
              {s.map(([x, y]) => <circle key={x} cx={sx(x)} cy={sy(y)} r={p === "Aqua" ? 2.6 : 1.8} fill="var(--ink)"><title>{`${NAME[p]} ${x}: ${fmtHour(y)}`}</title></circle>)}
            </g>
          );
        })}
        <text x={M.l} y={H - 4} fontSize="11" fill="var(--ink-2)">{`Year (${windowLabel} window, local solar date)`}</text>
      </svg>
      <figcaption>{title}. Median local solar time of daytime detections. Aqua is the thick line.</figcaption>
    </figure>
  );
}

/** Daily Aqua/S-NPP ratio vs overpass-time difference (charts_t2.ratio_vs_delta); era by marker shape. */
export function RatioChart({ data, region, title, splitYear }: { data: ChartsT2; region: string; title: string; splitYear: number }) {
  const pts = (data.ratio_vs_delta[region] ?? []).filter((d) => d.ratio > 0);
  if (pts.length === 0) return null;
  const xs = pts.map((d) => d.delta_h);
  const x0 = Math.floor(Math.min(...xs) * 2) / 2, x1 = Math.ceil(Math.max(...xs) * 2) / 2;
  const ly = pts.map((d) => Math.log10(d.ratio));
  const y0 = Math.floor(Math.min(...ly)), y1 = Math.ceil(Math.max(...ly));
  const sx = (x: number) => M.l + ((x - x0) / (x1 - x0)) * (W - M.l - M.r);
  const sy = (v: number) => H - M.b - ((Math.log10(v) - y0) / (y1 - y0)) * (H - M.t - M.b);
  const yt = Array.from({ length: y1 - y0 + 1 }, (_, k) => Math.pow(10, y0 + k));
  return (
    <figure className="chart" data-testid={`chart-ratio-${region}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${title}: daily Aqua to S-NPP ratio against the overpass time difference, ${pts.length} days`}>
        {yt.map((t) => (
          <g key={t}>
            <line x1={M.l} x2={W - M.r} y1={sy(t)} y2={sy(t)} stroke="var(--rule)" />
            <text x={M.l - 6} y={sy(t) + 4} textAnchor="end" fontSize="11" fill="var(--ink-2)">{t >= 1 ? t.toFixed(0) : t.toPrecision(1)}</text>
          </g>
        ))}
        {niceTicks(x0, x1, 6).map((t) => (
          <g key={t}>
            <line x1={sx(t)} x2={sx(t)} y1={M.t} y2={H - M.b} stroke="var(--rule)" strokeDasharray={t === 0 ? "" : "2 4"} />
            <text x={sx(t)} y={H - M.b + 18} textAnchor="middle" fontSize="11" fill="var(--ink-2)">{t > 0 ? `+${t}` : t} h</text>
          </g>
        ))}
        {pts.map((d) => {
          const late = Number(d.date.slice(0, 4)) >= splitYear;
          const x = sx(d.delta_h), y = sy(d.ratio);
          return late ? (
            <path key={d.date} d={`M${x - 3},${y - 3}L${x + 3},${y + 3}M${x - 3},${y + 3}L${x + 3},${y - 3}`} stroke="var(--warn)" strokeWidth="1.4"><title>{`${d.date}: ratio ${d.ratio}, Δ ${d.delta_h} h`}</title></path>
          ) : (
            <circle key={d.date} cx={x} cy={y} r="2.3" fill="none" stroke="var(--accent)" strokeWidth="1"><title>{`${d.date}: ratio ${d.ratio}, Δ ${d.delta_h} h`}</title></circle>
          );
        })}
        <g transform={`translate(${W - M.r + 8}, ${M.t + 10})`} fontSize="11.5" fill="var(--ink)">
          <circle cx="4" cy="0" r="3" fill="none" stroke="var(--accent)" /><text x="12" y="4">before {splitYear}</text>
          <path d="M1,15L7,21M1,21L7,15" stroke="var(--warn)" strokeWidth="1.4" /><text x="12" y="22">{splitYear} on</text>
        </g>
        <text x={M.l} y={H - 4} fontSize="11" fill="var(--ink-2)">Aqua minus S-NPP overpass time, hours (log ratio on the vertical axis)</text>
      </svg>
      <figcaption>{title}. One mark per day with both Aqua and S-NPP daytime fire ({pts.length} days).</figcaption>
    </figure>
  );
}

type LineSeries = { key: string; name: string; dash: string; width: number; marker: "circle" | "square" | "triangle" | "diamond"; pts: [number, number][] };

function Marker({ kind, x, y, title }: { kind: LineSeries["marker"]; x: number; y: number; title: string }) {
  const t = <title>{title}</title>;
  if (kind === "square") return <rect x={x - 2.6} y={y - 2.6} width="5.2" height="5.2" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="1.2">{t}</rect>;
  if (kind === "triangle") return <path d={`M${x},${y - 3.4}L${x + 3.2},${y + 2.4}H${x - 3.2}Z`} fill="var(--ink)">{t}</path>;
  if (kind === "diamond") return <path d={`M${x},${y - 3.4}L${x + 3.4},${y}L${x},${y + 3.4}L${x - 3.4},${y}Z`} fill="var(--sheet)" stroke="var(--ink)" strokeWidth="1.2">{t}</path>;
  return <circle cx={x} cy={y} r="2.6" fill="var(--ink)">{t}</circle>;
}

/** Multi-line chart by year; lines differ by dash and marker shape and carry direct end labels. */
function YearLines({ series, title, label, yFmt, log, refLine, testid, yTitle }: { series: LineSeries[]; title: string; label: string; yFmt: (v: number) => string; log?: boolean; refLine?: number; testid: string; yTitle: string }) {
  const all = series.flatMap((s) => s.pts).filter(([, v]) => !log || v > 0);
  if (all.length === 0) return null;
  const tf = (v: number) => (log ? Math.log10(v) : v);
  const x0 = Math.min(...all.map((p) => p[0])), x1 = Math.max(...all.map((p) => p[0]));
  const vs = all.map((p) => tf(p[1])).concat(refLine !== undefined ? [tf(refLine)] : []);
  let y0 = Math.min(...vs), y1 = Math.max(...vs);
  if (log) { y0 = Math.floor(y0); y1 = Math.ceil(y1); } else { const pad = (y1 - y0) * 0.15 || 0.05; y0 -= pad; y1 += pad; }
  const sx = (x: number) => M.l + ((x - x0) / Math.max(1, x1 - x0)) * (W - M.l - M.r);
  const sy = (v: number) => H - M.b - ((tf(v) - y0) / (y1 - y0)) * (H - M.t - M.b);
  const yt = log ? Array.from({ length: y1 - y0 + 1 }, (_, k) => Math.pow(10, y0 + k)) : niceTicks(y0, y1, 5);
  const ends = series.filter((s) => s.pts.length).map((s) => ({ name: s.name, y: sy(s.pts[s.pts.length - 1]![1]) })).sort((a, b) => a.y - b.y);
  for (let k = 1; k < ends.length; k++) ends[k]!.y = Math.max(ends[k]!.y, ends[k - 1]!.y + 13);
  return (
    <figure className="chart" data-testid={testid}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${title}. ${label}`}>
        {yt.map((t) => (
          <g key={t}>
            <line x1={M.l} x2={W - M.r} y1={sy(t)} y2={sy(t)} stroke="var(--rule)" />
            <text x={M.l - 6} y={sy(t) + 4} textAnchor="end" fontSize="11" fill="var(--ink-2)">{yFmt(t)}</text>
          </g>
        ))}
        {refLine !== undefined && <line x1={M.l} x2={W - M.r} y1={sy(refLine)} y2={sy(refLine)} stroke="var(--ink-2)" strokeDasharray="5 3" />}
        {niceTicks(x0, x1, Math.min(7, x1 - x0 || 1)).filter((t) => Number.isInteger(t)).map((t) => (
          <text key={t} x={sx(t)} y={H - M.b + 18} textAnchor="middle" fontSize="11" fill="var(--ink-2)">{t}</text>
        ))}
        {series.map((s) => (
          <g key={s.key}>
            <polyline fill="none" stroke="var(--ink)" strokeWidth={s.width} strokeDasharray={s.dash} points={s.pts.map(([x, v]) => `${sx(x)},${sy(v)}`).join(" ")} />
            {s.pts.map(([x, v]) => <Marker key={x} kind={s.marker} x={sx(x)} y={sy(v)} title={`${s.name} ${x}: ${yFmt(v)}`} />)}
          </g>
        ))}
        {ends.map((e) => <text key={e.name} x={W - M.r + 6} y={e.y + 4} fontSize="11.5" fill="var(--ink)">{e.name}</text>)}
        <text x={M.l} y={H - 4} fontSize="11" fill="var(--ink-2)">{yTitle}</text>
      </svg>
      <figcaption>{title}. {label}</figcaption>
    </figure>
  );
}

const yearPts = (o: Record<string, number>): [number, number][] => Object.entries(o).map(([y, v]) => [Number(y), v] as [number, number]).sort((a, b) => a[0] - b[0]);
const pick = <T,>(o: Record<string, T>, f: (t: T) => number) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, f(v)]));
const intFmt = (v: number) => (v >= 1 ? Math.round(v).toLocaleString("en-GB") : String(v));

/** VIIRS day vs night detections by year, S-NPP and NOAA-20 (t3 A2), log scale. */
export function DayNightChart({ data, title, windowLabel }: { data: T3Region; title: string; windowLabel: string }) {
  const a = data.a2_viirs_only;
  const series: LineSeries[] = [
    { key: "sd", name: "S-NPP day", dash: "", width: 2.2, marker: "circle", pts: yearPts(pick(a.snpp, (d) => d.day)) },
    { key: "nd", name: "NOAA-20 day", dash: "6 4", width: 1.4, marker: "square", pts: yearPts(pick(a.noaa20, (d) => d.day)) },
    { key: "sn", name: "S-NPP night", dash: "2 3", width: 2.2, marker: "triangle", pts: yearPts(pick(a.snpp, (d) => d.night)) },
    { key: "nn", name: "NOAA-20 night", dash: "10 3 2 3", width: 1.4, marker: "diamond", pts: yearPts(pick(a.noaa20, (d) => d.night)) },
  ];
  return <YearLines testid="chart-daynight" series={series} title={title} log yFmt={intFmt} yTitle={`Year (${windowLabel} window); detections, log scale`} label="VIIRS detections by day and by night, per year; day and night never added together. Values in the table below." />;
}

/** NOAA-20 / S-NPP detection ratio by year (t3 A1), one line per region, reference at 1. */
export function N20RatioChart({ data, names, title }: { data: Record<string, T3Region>; names: Record<string, string>; title: string }) {
  const marks: LineSeries["marker"][] = ["circle", "square", "triangle"];
  const dashes = ["", "6 4", "2 3"];
  const series: LineSeries[] = Object.entries(data).map(([r, d], k) => ({ key: r, name: names[r] ?? r, dash: dashes[k % 3]!, width: k === 0 ? 2 : 1.4, marker: marks[k % 3]!, pts: yearPts(pick(d.a1_noaa20_snpp.by_year, (v) => v.ratio)) }));
  return <YearLines testid="chart-n20ratio" series={series} title={title} refLine={1} yFmt={(v) => v.toFixed(2)} yTitle="Year; NOAA-20 / S-NPP detections (dashed line = 1)" label="Ratio of NOAA-20 to S-NPP detections on common days, per year and region. Values in the table below." />;
}
