"use client";
import { forwardRef } from "react";
import { fmtCount, fmtRatio } from "@/lib/format";
import { parseYm, ymLabel } from "@/lib/months";
import type { NrtMonth, NrtResult } from "@/lib/nrt";
import type { AreaDoc, Platform } from "@/lib/types";
import type { CustomDoc } from "@/lib/series";

interface Props {
  doc: AreaDoc | CustomDoc;
  latest: string;
  nrt: NrtResult | null;
}

function compare(v: number | null, med: number | null): string {
  if (v === null || med === null) return "no median for this month";
  if (med === 0) return v === 0 ? "same as the median" : "median is zero";
  const r = v / med;
  return `${fmtRatio(r)}× the median`;
}

function Figure({ what, v, med, years, testid, excl }: { what: string; v: number | null; med: number | null; years: [number, number]; testid: string; excl?: { med: number | null; excluded: number[] } | null }) {
  return (
    <div className="figure" data-testid={testid}>
      <span className="what">{what}</span>
      <span className="big num">{fmtCount(v)}</span>
      <span className="vs num" data-testid={`${testid}-all`}>
        {excl ? "All years: " : ""}median {fmtCount(med)} ({years[0]}–{years[1]}); {compare(v, med)}{excl ? " (the ratio uses this median)" : ""}
      </span>
      {excl && (
        <span className="vs num" data-testid={`${testid}-excl`}>
          {excl.excluded.length
            ? <>Excluding years we flag ({excl.excluded.join(", ")}): median {fmtCount(excl.med)}; {compare(v, excl.med)}</>
            : <>Excluding years we flag: none flagged for this area, same median</>}
        </span>
      )}
    </div>
  );
}

/** Provisional NOAA-20 NRT month so far vs the NOAA-20 standard median of that calendar month (D-010). */
function NrtFigure({ d, doc }: { d: NrtMonth; doc: AreaDoc | CustomDoc }) {
  const mi = parseYm(d.month).m - 1;
  const own = doc.median.NOAA20;
  const med = d.median ?? { value: own.values[mi] ?? null, years: own.baseline_years };
  const complete = d.daysCovered >= d.daysInMonth;
  return (
    <div className="figure nrt" data-testid="card-nrt">
      <span className="what">NOAA-20 VIIRS, {ymLabel(d.month)} <span className="tag">{d.label}</span></span>
      <span className="big num">{fmtCount(d.noaa20)}</span>
      <span className="vs num">
        {complete
          ? <>median {fmtCount(med.value)} ({med.years[0]}–{med.years[1]}); {compare(d.noaa20, med.value)}</>
          : <>{d.daysCovered} of {d.daysInMonth} days so far; full-month median {fmtCount(med.value)} ({med.years[0]}–{med.years[1]}), not comparable until the month ends</>}
        {d.geometry === "bbox" ? "; counted on the area's bounding box" : ""}
      </span>
    </div>
  );
}

/** Latest month vs same-month median. Offline build: cached archive snapshot, never presented as live. */
export const MonthCard = forwardRef<HTMLDivElement, Props>(function MonthCard({ doc, latest, nrt }, ref) {
  const months: string[] = [];
  const { y: fy, m: fm } = parseYm(doc.period.first);
  for (let i = 0; i < doc.period.n_months; i++) {
    const t = fy * 12 + fm - 1 + i;
    months.push(`${Math.floor(t / 12)}-${String((t % 12) + 1).padStart(2, "0")}`);
  }
  const i = months.indexOf(latest);
  const mi = parseYm(latest).m - 1;
  const h = i >= 0 ? (doc.harmonized.value[i] ?? null) : null;
  const n20: Platform = "NOAA20";
  const n = i >= 0 ? (doc.raw[n20].n[i] ?? null) : null;
  const prov = i >= 0 && doc.harmonized.provisional?.[i] === true;
  const hm = doc.median.harmonized;
  const nm = doc.median[n20];
  return (
    <div className="card" ref={ref} data-testid="month-card">
      <h2>
        {ymLabel(latest)}
        <span className="tag" data-testid="snapshot-label">Latest available month, not live{prov ? " · provisional" : ""}</span>
      </h2>
      <Figure testid="card-harmonized" what={`Harmonized, ${doc.units.harmonized}`} v={h} med={hm.values[mi] ?? null} years={hm.baseline_years} excl={doc.median_excl_flagged ? { med: doc.median_excl_flagged.values[mi] ?? null, excluded: doc.median_excl_flagged.excluded_years } : null} />
      <Figure testid="card-noaa20" what={`NOAA-20 VIIRS alone (${i >= 0 && doc.raw[n20].provisional?.[i] ? "near-real-time, provisional" : "standard archive"})`} v={n} med={nm.values[mi] ?? null} years={nm.baseline_years} />
      {nrt?.status === "ok" && <NrtFigure d={nrt.data} doc={doc} />}
      <p className="foot">
        Medians use complete months only. The month is the local solar month; &ldquo;current fire&rdquo; is read at month level.{" "}
        {nrt?.status === "ok" ? `The ${nrt.data.label} figure is FIRMS ${nrt.data.source}, filtered and masked like the archive, and will change when the standard data replace it.` : nrt?.status === "unavailable" && nrt.reason !== "No near-real-time service in this build." ? `Near-real-time data could not be loaded (${nrt.reason}), so this card shows the latest month in the saved data.` : `The live near-real-time service is not part of this build, so this card shows the latest month in the saved data.`}
      </p>
      {prov && <p className="foot" data-testid="card-provisional-note">This month uses FIRMS near-real-time data. It is provisional and will change when the standard data replace it. The year is not yet covered by our tests.</p>}
      <p className="foot" data-testid="card-live-note">
        The live current month appears here when the near-real-time service is switched on at launch.
      </p>
    </div>
  );
});
