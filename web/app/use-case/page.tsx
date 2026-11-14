import type { Metadata } from "next";
import { fmtCount, fmtNum } from "@/lib/format";
import { ymLabel } from "@/lib/months";
import { readData } from "@/lib/server";
import { checkMonth, flagshipMonth, type MonthCheck } from "@/lib/usecase";
import type { AreaDoc, IndexDoc } from "@/lib/types";

export const metadata: Metadata = { title: "Use case · Blind Spot" };

// The worked examples. Districts are chosen here; the headline month follows the D-042 rule
// (highest unflagged November since 2012, `flagshipMonth`); the contrast month is November 2025,
// a flagged year. Every number below is read from public/data at build time (CLAUDE.md rule 7).
const CONTRAST_MONTH = "2025-11";
const CASES = [
  { name: "Sangrur", country: "IND", slug: "sangrur", who: "A district officer in Sangrur, Indian Punjab" },
  { name: "Kasur", country: "PAK", slug: "kasur", who: "A district officer in Kasur, Pakistani Punjab, across the border from the Indian districts" },
] as const;
type CaseDef = (typeof CASES)[number];

const ratio = (a: number | null, b: number | null) => (a === null || b === null || b === 0 ? null : a / b);

function Shot({ slug, step, alt }: { slug: string; step: string; alt: string }) {
  // Screenshots are written by `make web-test` (e2e/run.mjs) into public/usecase/.
  // eslint-disable-next-line @next/next/no-img-element -- static export, no image optimizer
  return <img className="shot" src={`/usecase/${slug}-${step}.png`} alt={alt} loading="lazy" width={1200} height={700} />;
}

function Case({ c, doc, id, month, contrast, nEligible }: { c: CaseDef; doc: AreaDoc; id: string; month: string; contrast: boolean; nEligible: number }) {
  const MONTH = month;
  const slug = contrast ? `${c.slug}-flagged` : c.slug;
  const k: MonthCheck = checkMonth(doc, MONTH);
  const r = ratio(k.value, k.median), rn = ratio(k.noaa20, k.noaa20Median);
  const lowest = k.minEarlier && k.value !== null && k.value < k.minEarlier.value;
  const href = `/?area=${id}&from=2003-01&to=${MONTH}`;
  const unit = doc.units.harmonized;
  return (
    <section className="usecase" data-testid={`usecase-${slug}`} aria-labelledby={`h-${slug}`}>
      <h2 id={`h-${slug}`}>{c.name}, {ymLabel(MONTH)}{contrast ? ": a flagged year, for contrast" : ": the highest-burning unflagged November"}</h2>
      {contrast
        ? <p className="hint" data-testid={`uc-caption-${slug}`}><strong>Contrast example.</strong> {MONTH.slice(0, 4)} is on our own caution list for this district, so the record is less comparable. This is what the caution looks like; it is not the headline example.</p>
        : <p className="hint" data-testid={`uc-caption-${slug}`}><strong>Headline example.</strong> Picked by a rule fixed in advance: of the {nEligible} Novembers since 2012 that are complete and not flagged for this district, {MONTH.slice(0, 4)} has the highest harmonized count.</p>}
      <p>{c.who} wants to know whether stubble burning in {ymLabel(MONTH)} was unusual, and whether the satellite record can be trusted for that month.</p>
      <ol className="steps">
        <li>
          <h3>Open the district</h3>
          <p>In the <a href={href}>Explorer</a>, type &ldquo;{c.name}&rdquo; in <em>Find a district</em> and press Enter (or open <a href={href} data-testid={`link-${slug}`}>this link</a>). The calendar shows one cell per month since {doc.period.first.slice(0, 4)}.</p>
          <Shot slug={slug} step="1" alt={`Explorer with ${c.name} selected: map, month card and burning calendar`} />
        </li>
        <li>
          <h3>Read the {ymLabel(MONTH)} cell</h3>
          <p>Hover or focus the {ymLabel(MONTH)} cell. It reads <strong className="num" data-testid={`uc-value-${slug}`}>{fmtCount(k.value)}</strong> {unit} ({k.source === "SNPP" ? "S-NPP VIIRS as observed" : k.source}{k.partial ? ", partial month" : ""}).</p>
          <Shot slug={slug} step="2" alt={`Calendar readout for November ${MONTH.slice(0, 4)} in ${c.name}`} />
        </li>
        <li>
          <h3>Compare with a normal November</h3>
          <p>
            The November median over {k.medianYears[0]}–{k.medianYears[1]} ({k.medianN} complete Novembers) is <strong className="num" data-testid={`uc-median-${slug}`}>{fmtCount(k.median)}</strong>
            {r !== null ? <>, so {ymLabel(MONTH)} is <strong className="num">{fmtNum(r, 2)}×</strong> the median</> : null}.
            {k.rankFromLowest !== null && <> It ranks <span className="num">{k.rankFromLowest}</span> of <span className="num">{k.nCompared}</span> Novembers from the lowest.</>}
            {k.minEarlier && k.maxEarlier && <> Earlier Novembers ranged from <span className="num">{fmtCount(k.minEarlier.value)}</span> ({k.minEarlier.year}) to <span className="num">{fmtCount(k.maxEarlier.value)}</span> ({k.maxEarlier.year}){lowest ? ", so this November is below every earlier one" : ""}.</>}
            {k.medianExcl !== null && <> Leaving out the years we flag ({k.excludedYears.join(", ") || "none"}) the median is <span className="num" data-testid={`uc-median-excl-${slug}`}>{fmtCount(k.medianExcl)}</span>.</>}
            {" "}The median includes {MONTH.slice(0, 4)} itself; it is the app&rsquo;s fixed baseline, not a test.
          </p>
        </li>
        <li>
          <h3>Check the same satellite on its own</h3>
          <p>Switch to <em>Raw</em> → <em>NOAA-20 VIIRS</em>. NOAA-20 alone counted <strong className="num" data-testid={`uc-n20-${slug}`}>{fmtCount(k.noaa20)}</strong> hotspots against its own November median of <span className="num">{fmtCount(k.noaa20Median)}</span> ({k.noaa20Years[0]}–{k.noaa20Years[1]}){rn !== null ? <>, <span className="num">{fmtNum(rn, 2)}×</span></> : null}. A second satellite with a separate record tells the same story only if the two ratios point the same way.</p>
        </li>
        <li>
          <h3>Read the reliability flag before concluding</h3>
          {k.flag ? (
            <>
              <p data-testid={`uc-flag-${slug}`}>{MONTH.slice(0, 4)} carries a <strong>caution</strong> flag (inherited from its calibration region, {doc.reliability?.calib_region.replace("_", " ")}):</p>
              <ul>{k.flagText.map((t) => <li key={t}>{t}.</li>)}</ul>
            </>
          ) : <p data-testid={`uc-flag-${slug}`}>{MONTH.slice(0, 4)} carries no reliability flag for this district (other years are flagged; see the notes below the calendar).</p>}
          <Shot slug={slug} step="3" alt={`Caution notes below the calendar for ${c.name}`} />
        </li>
        <li>
          <h3>What the officer can say</h3>
          <p data-testid={`uc-conclusion-${slug}`}>
            {r !== null && r < 1 ? `Fewer afternoon-satellite hotspots than a typical November` : r !== null && r > 1 ? `More afternoon-satellite hotspots than a typical November` : `No comparison possible`}
            {r !== null ? ` (${fmtNum(r, 2)}× the median)` : ""}.
            {k.flag?.reasons.some((x) => x.code === "burning_time_shift") ? " Because some burning has moved past the afternoon satellites, the drop in the record may be larger than the drop on the ground; it is not proof that burning stopped." : ""}
            {k.flag?.reasons.some((x) => x.code === "aqua_overpass_drift") ? " The MODIS-to-VIIRS factor cannot be re-checked this year, but from 2012 the calendar is S-NPP as observed, so this month does not depend on it." : ""}
            {" "}Download the calendar CSV to attach the numbers to a report.
          </p>
        </li>
      </ol>
    </section>
  );
}

export default function UseCase() {
  const index = readData<IndexDoc>("index.json");
  const found = CASES.map((c) => ({ c, d: index.districts.find((d) => d.name === c.name && d.country === c.country) })).filter((x): x is { c: CaseDef; d: NonNullable<typeof x.d> } => !!x.d);
  const docs = found.map(({ c, d }) => ({ c, id: d.id, doc: readData<AreaDoc>(`districts/${d.id}.json`) }));
  const heads = docs.map((x) => ({ ...x, f: flagshipMonth(x.doc) })).filter((x): x is typeof x & { f: NonNullable<typeof x.f> } => x.f !== null);
  return (
    <main id="main" className="page">
      <h1>Use case: was that November abnormal?</h1>
      <p>Worked examples, step by step. Each headline month is the highest-burning November since 2012 that is not on our caution list for that district, found by a rule fixed before looking. Below them, November {CONTRAST_MONTH.slice(0, 4)} is shown as a contrast, because it is a flagged year. Every number on this page is read from the same district files the Explorer uses. The record ends {ymLabel(index.period.last)}.</p>
      {heads.map(({ c, id, doc, f }) => <Case key={c.slug} c={c} id={id} doc={doc} month={f.ym} contrast={false} nEligible={f.nEligible} />)}
      <h2>Contrast: November {CONTRAST_MONTH.slice(0, 4)}, a flagged year</h2>
      {docs.map(({ c, id, doc }) => <Case key={`${c.slug}-flagged`} c={c} id={id} doc={doc} month={CONTRAST_MONTH} contrast nEligible={0} />)}
    </main>
  );
}
