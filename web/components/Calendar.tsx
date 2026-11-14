"use client";
import { forwardRef, useMemo, useRef, useState } from "react";
import { cividis, scaleT, textOn } from "@/lib/cividis";
import { fmtCount } from "@/lib/format";
import { monthLong, monthShort, parseYm } from "@/lib/months";
import { flagSentence, plainReason, REGION_SHORT, type Flags } from "@/lib/reliability";
import type { Era, Series } from "@/lib/types";

interface Props {
  series: Series;
  eras: Era[];
  range: [string, string];
  showValues: boolean;
  /** Reliability flags (D-039/D-040); null when the data carries none. */
  flags?: Flags | null;
}

interface Cell {
  ym: string;
  y: number;
  m: number;
  i: number;
  v: number | null;
  partial: boolean;
  provisional: boolean;
  source: string | null;
  inRange: boolean;
}

const SOURCE_TEXT: Record<string, string> = {
  Aqua: "Aqua MODIS",
  Terra: "Terra MODIS",
  SNPP: "S-NPP VIIRS",
  NOAA20: "NOAA-20 VIIRS",
};

export function describe(c: Cell, s: Series, harmonized: boolean, flags?: Flags | null): string {
  const fy = flags?.years.get(c.y);
  const flag = fy && flags ? `. ${flagSentence(fy, flags)}` : "";
  return describeValue(c, s, harmonized) + flag;
}

/** Warning triangle with an exclamation mark; drawn in currentColor so it follows the theme. */
export function FlagIcon({ size = 14 }: { size?: number }) {
  return (
    <svg className="flag-icon" width={size} height={size} viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M8 1.5 15 14.5H1z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M8 6v4.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="8" cy="12.3" r="1" fill="currentColor" />
    </svg>
  );
}

function describeValue(c: Cell, s: Series, harmonized: boolean): string {
  const when = `${monthLong(c.m)} ${c.y}`;
  if (c.v === null) return `${when}: no data${c.inRange ? "" : ", outside selected period"}`;
  const src = c.source ? (SOURCE_TEXT[c.source] ?? c.source) : "";
  const how = harmonized && c.source === "Aqua" ? `${src} scaled to S-NPP` : src;
  return `${when}: ${fmtCount(c.v)} ${s.unit.split(" (")[0]}${how ? `, ${how}` : ""}${c.partial ? ", partial month" : ""}${c.provisional ? ", provisional (near-real-time, will change)" : ""}${c.inRange ? "" : ", outside selected period"}`;
}

/** True when the sensor-switch line runs above month (y, m): the 12 months starting at the seam month. */
export function seamEdge(y: number, m: number, seam: { y: number; m: number } | null): boolean {
  if (!seam) return false;
  return (y === seam.y && m >= seam.m) || (y === seam.y + 1 && m < seam.m);
}

/** Month x year calendar heatmap. Roving tabindex grid: arrows, Home/End move focus; values in tooltip + readout. */
export const Calendar = forwardRef<HTMLDivElement, Props>(function Calendar({ series, eras, range, showValues, flags = null }, ref) {
  const harmonized = series.label.startsWith("Harmonized");
  const { years, grid, max } = useMemo(() => {
    const cells: Cell[] = series.months.map((ym, i) => {
      const { y, m } = parseYm(ym);
      const v = series.value[i] ?? null;
      return { ym, y, m, i, v, partial: series.partial[i] === true, provisional: series.provisional?.[i] === true, source: series.source[i] ?? null, inRange: ym >= range[0] && ym <= range[1] };
    });
    const ys = Array.from(new Set(cells.map((c) => c.y))).sort((a, b) => a - b);
    const g = new Map(cells.map((c) => [c.ym, c]));
    const mx = Math.max(0, ...cells.filter((c) => c.inRange && c.v !== null).map((c) => c.v as number));
    return { years: ys, grid: g, max: mx };
  }, [series, range]);

  const flagged = useMemo(() => (flags ? [...flags.years.values()].filter((fy) => fy.year >= Number(range[0].slice(0, 4)) && fy.year <= Number(range[1].slice(0, 4))).sort((a, b) => a.year - b.year) : []), [flags, range]);
  const [focus, setFocus] = useState<{ r: number; c: number }>({ r: 0, c: 0 });
  const [hover, setHover] = useState<Cell | null>(null);
  const [tipPos, setTipPos] = useState<{ x: number; y: number } | null>(null);
  const [active, setActive] = useState<Cell | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  const cellAt = (r: number, c: number) => grid.get(`${years[r]}-${String(c + 1).padStart(2, "0")}`);
  const seamYm = eras.find((e) => e.source === "SNPP")?.start ?? null;
  const seam = seamYm ? parseYm(seamYm) : null;

  const show = (c: Cell, target: HTMLElement) => {
    const host = gridRef.current?.getBoundingClientRect();
    const b = target.getBoundingClientRect();
    if (host) {
      // Anchored to the cell; clamped so a wrapped tooltip never leaves the grid (phone width).
      const half = Math.min(144, host.width / 2);
      setTipPos({ x: Math.min(host.width - half, Math.max(half, b.left - host.left + b.width / 2)), y: b.top - host.top });
    }
    setHover(c);
    setActive(c);
  };

  const onKey = (e: React.KeyboardEvent) => {
    let { r, c } = focus;
    const last = years.length - 1;
    switch (e.key) {
      case "ArrowRight": c = Math.min(11, c + 1); break;
      case "ArrowLeft": c = Math.max(0, c - 1); break;
      case "ArrowDown": r = Math.min(last, r + 1); break;
      case "ArrowUp": r = Math.max(0, r - 1); break;
      case "Home": c = 0; if (e.ctrlKey) r = 0; break;
      case "End":
        c = 11;
        if (e.ctrlKey) {
          // Last month of the record, not a trailing "outside the archive" cell when the last year is partial.
          r = last;
          while (c > 0 && !cellAt(r, c)) c--;
        }
        break;
      case "Escape": setHover(null); return;
      default: return;
    }
    e.preventDefault();
    setFocus({ r, c });
    const btn = gridRef.current?.querySelector<HTMLElement>(`[data-rc="${r}-${c}"]`);
    btn?.focus();
  };

  // Era band split by the seam month: rows wholly before the switch are MODIS; a mixed row
  // (seam not in January) goes to the VIIRS band and the stepped seam line marks the month.
  const seamKey = seam ? seam.y * 12 + seam.m : null;
  const modisRows = seamKey !== null ? years.filter((y) => y * 12 + 12 < seamKey).length : 0;
  const viirsRows = years.length - modisRows;
  const eraLabel = (src: string) => eras.find((e) => e.source === src)?.label ?? src;

  return (
    <div ref={ref}>
      <div className="cal num" role="grid" aria-label={`${series.label}: months by year. Use arrow keys to move between months.`} aria-rowcount={years.length + 1} ref={gridRef} onKeyDown={onKey} data-testid="calendar">
        <div role="row" style={{ display: "contents" }}>
          <span role="columnheader"><span className="sr-only">Sensor era</span></span>
          <span role="columnheader"><span className="sr-only">Year</span></span>
          {Array.from({ length: 12 }, (_, k) => (
            <span key={k} role="columnheader" className="mh" aria-label={monthLong(k + 1)}>{monthShort(k + 1).slice(0, 1)}<span className="sr-only">{monthShort(k + 1).slice(1)}</span></span>
          ))}
          <span role="columnheader"><span className="sr-only">Reliability</span></span>
        </div>
        {modisRows > 0 && (
          <div className="era modis" aria-hidden="true" style={{ gridColumn: 1, gridRow: `2 / span ${modisRows}`, ["--span" as string]: modisRows }} title={eraLabel("Aqua")}>{harmonized ? eraLabel("Aqua") : "MODIS"}</div>
        )}
        {viirsRows > 0 && (
          <div className="era viirs" aria-hidden="true" style={{ gridColumn: 1, gridRow: `${2 + modisRows} / span ${viirsRows}` }}>{harmonized ? eraLabel("SNPP") : "VIIRS"}</div>
        )}
        {years.map((y, r) => (
          <div role="row" key={y} style={{ display: "contents" }}>
            <span role="rowheader" className={`yr${flags?.years.has(y) ? " flag" : ""}`} style={{ gridColumn: 2, gridRow: r + 2 }}>{y}</span>
            {Array.from({ length: 12 }, (_, c) => {
              const cell = cellAt(r, c);
              const isFocus = focus.r === r && focus.c === c;
              if (!cell) {
                return <span key={c} role="gridcell" aria-label={`${monthLong(c + 1)} ${y}: outside the archive`} className="cell nodata" style={{ gridColumn: c + 3, gridRow: r + 2 }} tabIndex={isFocus ? 0 : -1} data-rc={`${r}-${c}`} />;
              }
              const t = cell.v === null ? 0 : scaleT(cell.v, max);
              const label = describe(cell, series, harmonized, flags);
              const cls = ["cell", cell.v === null ? "nodata" : "", cell.partial ? "partial" : "", cell.provisional ? "prov" : "", cell.inRange ? "" : "out", seamEdge(y, c + 1, seam) ? "seam" : ""].join(" ");
              return (
                <span
                  key={c}
                  role="gridcell"
                  className={cls}
                  data-rc={`${r}-${c}`}
                  data-ym={cell.ym}
                  aria-label={label}
                  tabIndex={isFocus ? 0 : -1}
                  style={{ gridColumn: c + 3, gridRow: r + 2, background: cell.v === null ? undefined : cividis(t), color: cell.v === null ? "var(--ink-2)" : textOn(t) }}
                  onMouseEnter={(e) => show(cell, e.currentTarget)}
                  onClick={(e) => { setFocus({ r, c }); show(cell, e.currentTarget); }}
                  onMouseLeave={() => setHover(null)}
                  onFocus={(e) => { setFocus({ r, c }); show(cell, e.currentTarget); }}
                  onBlur={() => setHover(null)}
                >
                  {showValues && cell.v !== null && cell.inRange ? fmtCount(Math.round(cell.v)) : ""}
                </span>
              );
            })}
            {(() => {
              const fy = flags?.years.get(y);
              return (
                <span role="gridcell" className={`flagcell${fy ? " on" : ""}`} style={{ gridColumn: 15, gridRow: r + 2 }} data-flag-year={fy ? y : undefined} title={fy && flags ? flagSentence(fy, flags) : undefined}>
                  {fy && flags ? <><FlagIcon /><span className="sr-only">{`${y}: ${flagSentence(fy, flags)}`}</span></> : null}
                </span>
              );
            })()}
          </div>
        ))}
        {hover && tipPos && (
          <div className="tip" role="tooltip" style={{ left: tipPos.x, top: tipPos.y }} data-testid="tooltip">{describe(hover, series, harmonized, flags)}</div>
        )}
      </div>
      <p className="readout num" aria-live="polite" data-testid="readout">{active ? describe(active, series, harmonized, flags) : "Hover or focus a month to read its exact value."}</p>
      <div className="legend" data-testid="legend">
        <div className="ramp">
          <span>{series.unit.split(" (")[0]} per month, square-root scale</span>
          <div className="bar" style={{ background: `linear-gradient(90deg, ${Array.from({ length: 9 }, (_, k) => cividis(k / 8)).join(", ")})` }} />
          <div className="ticks num">
            {[0, 0.5, 1].map((t) => <span key={t}>{fmtCount(Math.round(max * t * t))}</span>)}
          </div>
        </div>
        <span className="key"><i style={{ background: "repeating-linear-gradient(-45deg, var(--nodata) 0 2px, transparent 2px 5px)" }} />No data (platform not flying, no factor, or month not yet in the archive)</span>
        <span className="key"><i style={{ position: "relative" }}><b style={{ position: "absolute", top: 2, right: 2, width: 4, height: 4, borderRadius: "50%", background: "currentColor" }} /></i>Dot: partial month, left out of medians</span>
        <span className="key"><i style={{ background: "repeating-linear-gradient(45deg, var(--hatch) 0 4px, transparent 4px 8px)" }} />Hatched band: MODIS era{harmonized ? ", scaled to S-NPP" : ""}</span>
        {series.provisional?.some(Boolean) && <span className="key" data-testid="legend-provisional"><i className="prov-key" />Dashed outline: provisional month (near-real-time data, will change)</span>}
        {flags && flags.years.size > 0 && <span className="key"><i className="flag-key"><FlagIcon size={12} /></i>Triangle and striped year: caution year (see notes below)</span>}
        {seam && <span className="key"><i style={{ borderTop: "2px solid var(--ink)" }} />Stepped line: sensor switch ({monthLong(seam.m)} {seam.y})</span>}
      </div>
      {flagged.length > 0 && flags && (
        <div className="flag-notes" data-testid="flag-notes">
          <h3><FlagIcon /> Caution years in this period</h3>
          <p>The harmonized record is less comparable in these years. Values are shown as computed; read them with the reason in mind. Source: the T3 tests (Results page){flags.regions.length > 1 ? `; flags of every calibration region this area overlaps: ${flags.regions.map((x) => REGION_SHORT[x] ?? x).join(", ")}` : ""}.</p>
          <ul>
            {flagged.map((fy) => (
              <li key={fy.year} data-testid={`flag-note-${fy.year}`}>
                <strong>{fy.year}</strong>{" "}
                {fy.reasons.map((r, k) => (
                  <span key={r.code}>{k > 0 ? "; " : ""}{plainReason(r.code, flags.codeText)}{flags.regions.length > 1 ? ` (${r.regions.map((x) => REGION_SHORT[x] ?? x).join(", ")})` : ""}</span>
                ))}.
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
});
