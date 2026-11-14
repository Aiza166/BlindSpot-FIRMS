import type { Metadata } from "next";
import { DayNightChart, N20RatioChart, OverpassChart, RatioChart } from "@/components/Charts";
import { plainReason } from "@/lib/reliability";
import { fmtPct, fmtNum } from "@/lib/format";
import { EXPLANATION, maxShare, meanShare, REGION_NAME, t3VerdictClass, verdictClass, type ChartsT2, type MaskReport, type T1, type T2, type T3 } from "@/lib/results";
import { readData } from "@/lib/server";

export const metadata: Metadata = { title: "Results · Blind Spot" };

function V({ label }: { label: string }) {
  return <span className={`verdict ${verdictClass(label)}`}>{label}</span>;
}

function windowText(w: { start: string; end: string }): string {
  const mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const f = (s: string) => { const [m, d] = s.split("-").map(Number); return `${d} ${mon[(m ?? 1) - 1]}`; };
  return `${f(w.start)} – ${f(w.end)}`;
}

export default function Results() {
  const t1 = readData<T1>("results/t1.json");
  const t2 = readData<T2>("results/t2.json");
  const charts = readData<ChartsT2>("results/charts_t2.json");
  const mask = readData<MaskReport>("results/mask_report.json");
  const t3 = readData<T3>("results/t3.json");
  const t3Win = windowText(t3.window);
  const short: Record<string, string> = { PK_Punjab: "PK Punjab", IN_Punjab: "IN Punjab", rest_of_box: "Control" };
  const regions = ["PK_Punjab", "IN_Punjab"] as const;
  const step = (r: string) => t1.results.hotspots[r]!.step_2012;
  const calib = t2.parameters.calib_years, test = t2.parameters.test_years;
  const span = (ys: number[]) => `${ys[0]}–${ys[ys.length - 1]}`;
  const ns = t2.t2b.IN_Punjab?.night_share.SNPP ?? {};
  const nsBase = meanShare(ns, calib), nsBaseMax = maxShare(ns, calib), nsTest = meanShare(ns, test);
  const later = nsTest !== null && nsBaseMax !== null && nsTest > nsBaseMax;
  const win = windowText(t1.window);
  const splitYear = test[0] ?? 0;

  return (
    <main id="main" className="page wide">
      <h1>What the tests found</h1>
      <p className="finding" data-testid="finding">
        Raw, Punjab&rsquo;s fire record jumps {fmtPct(step("PK_Punjab").raw_step, 0, true)} (Pakistan) and {fmtPct(step("IN_Punjab").raw_step, 0, true)} (India) in {t1.parameters.step_year}, when the record switches from MODIS to VIIRS.
        Harmonized, the step is {fmtPct(step("PK_Punjab").harmonized_step, 0, true)} and {fmtPct(step("IN_Punjab").harmonized_step, 0, true)}.
        {later && nsBase !== null && nsTest !== null ? ` Since ${splitYear}, more of Indian Punjab's S-NPP detections are at night (${fmtPct(nsTest, 2)} vs ${fmtPct(nsBase, 2)} in ${span(calib)}), consistent with burning moving later in the day.` : ""}
      </p>
      <p>Pre-registered regions are reported separately and never added together. Window {win}, {t1.window.time_basis}. Unit: hotspots, masked and filtered.</p>

      <nav className="toc" aria-label="On this page">
        <h2 className="toc-title">On this page</h2>
        <ol>
          <li><a href="#glance">At a glance</a></li>
          <li><a href="#t1">T1: the {t1.parameters.step_year} sensor step</a></li>
          <li><a href="#t2">T2: Aqua / S-NPP ratio</a></li>
          <li><a href="#t2b">T2b: night share</a></li>
          <li><a href="#t3">T3: why the ratio moved</a></li>
          <li><a href="#flags">Reliability flags</a></li>
          <li><a href="#mask">Mask report</a></li>
        </ol>
      </nav>

      <section aria-labelledby="glance" className="glance" data-testid="glance">
        <h2 id="glance">At a glance</h2>
        <p>One line per test and region. Labels are the pipeline&rsquo;s own words (pass, fail, inconclusive, drift); the reason is read from the same results files. Details follow below.</p>

        <article className="glance-test" aria-labelledby="g-t1">
          <h3 id="g-t1">T1. Does harmonization remove the {t1.parameters.step_year} sensor step?</h3>
          <div className="glance-regs">
            {regions.map((r) => {
              const s = step(r), f = t2.t1_reevaluated[r]!;
              return (
                <div key={r} className="glance-reg" data-testid={`glance-t1-${r}`}>
                  <h4>{REGION_NAME[r]}</h4>
                  <p><V label={f.label} /></p>
                  <p className="why">Raw step {fmtPct(s.raw_step, 0, true)}, harmonized step {fmtPct(s.harmonized_step, 1, true)}. Judged on: {f.basis}.</p>
                </div>
              );
            })}
          </div>
        </article>

        <article className="glance-test" aria-labelledby="g-t2">
          <h3 id="g-t2">T2. Is the Aqua / S-NPP ratio stable?</h3>
          <div className="glance-regs">
            {regions.map((r) => {
              const t = t2.t2[r]!;
              return (
                <div key={r} className="glance-reg" data-testid={`glance-t2-${r}`}>
                  <h4>{REGION_NAME[r]}</h4>
                  <p>Revised: <V label={t.verdict_revised.label} /> Pre-registered: <V label={t.verdict.label} /></p>
                  <p className="why">Test years that can be compared: {t.verdict_revised.evaluable_test_years.join(", ") || "none"}. Smallest drift we could detect: {fmtPct(t.min_detectable_drift.pct, 0)}.</p>
                </div>
              );
            })}
          </div>
        </article>

        <article className="glance-test" aria-labelledby="g-t3">
          <h3 id="g-t3">T3. Why did the ratio move: orbit, timing or a real decline?</h3>
          <div className="glance-regs">
            {regions.map((r) => (
              <div key={r} className="glance-reg" data-testid={`glance-t3-${r}`}>
                <h4>{REGION_NAME[r]}</h4>
                <ul className="glance-list">
                  {(["O", "T", "D"] as const).map((k) => {
                    const ev = t3.t3[r]?.evidence[k];
                    if (!ev) return null;
                    return (
                      <li key={k}>
                        <span>{EXPLANATION[k]}</span> <span className={`verdict ${t3VerdictClass(ev.verdict)}`}>{ev.verdict}</span>
                        <span className="why">{ev.supporting[0] ?? "no supporting evidence"}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        </article>
        <p className="hint">Read the limits before relying on a verdict: <a href="/methods/#limitations">Methods, limitations</a>.</p>
      </section>

      <h2 id="t1">T1: does harmonization remove the {t1.parameters.step_year} sensor step?</h2>
      <div className="table-wrap" role="region" aria-label="T1 verdicts (scrollable table)" tabIndex={0}><table data-testid="t1-table">
        <thead><tr><th>Region</th><th>Raw step</th><th>Harmonized step</th><th>Ratio (95% CI)</th><th>Pass if ratio &lt;</th><th>Held-out years inside PI</th><th>Final T1</th></tr></thead>
        <tbody>
          {regions.map((r) => {
            const s = step(r), h = t1.results.hotspots[r]!.heldout, f = t2.t1_reevaluated[r]!;
            return (
              <tr key={r}>
                <td>{REGION_NAME[r]}</td>
                <td className="num">{fmtPct(s.raw_step, 0, true)}</td>
                <td className="num">{fmtPct(s.harmonized_step, 1, true)}</td>
                <td className="num">{fmtNum(s.ratio, 3)} ({fmtNum(s.ratio_ci95[0], 3)}–{fmtNum(s.ratio_ci95[1], 3)})</td>
                <td className="num">{fmtNum(s.threshold, 2)}</td>
                <td className="num">{h.n_inside} of {h.n}</td>
                <td><V label={f.label} /><br /><small>{f.basis}</small></td>
              </tr>
            );
          })}
        </tbody>
      </table></div>
      <p>The held-out part ({span(t1.parameters.heldout_years)}) is judged only when T2 finds no drift (PLAN §4). That is why Pakistan&rsquo;s T1 rests on the step alone and India&rsquo;s includes the held-out years.</p>

      <h2 id="t2">T2: is the Aqua / S-NPP ratio stable?</h2>
      <div className="table-wrap" role="region" aria-label="T2 verdicts (scrollable table)" tabIndex={0}><table data-testid="t2-table">
        <thead><tr><th>Region</th><th>Pre-registered verdict</th><th>Revised verdict (D-034)</th><th>Evaluable test years</th><th>Smallest detectable drift</th><th>Aqua timing effect, per hour later</th></tr></thead>
        <tbody>
          {[...regions, "rest_of_box"].map((r) => {
            const t = t2.t2[r];
            if (!t) return null;
            return (
              <tr key={r}>
                <td>{REGION_NAME[r]}</td>
                <td>{r === "rest_of_box" ? <small>none (control)</small> : <V label={t.verdict.label} />}</td>
                <td><V label={t.verdict_revised.label} /></td>
                <td className="num">{t.verdict_revised.evaluable_test_years.join(", ") || "none"}</td>
                <td className="num">{fmtPct(t.min_detectable_drift.pct, 0)}</td>
                <td className="num">{fmtPct(t.aqua_drift_effect.effect_pct_per_hour, 0, true)} ({fmtPct(t.aqua_drift_effect.effect_ci95_pct_per_hour[0], 0)} to {fmtPct(t.aqua_drift_effect.effect_ci95_pct_per_hour[1], 0)})</td>
              </tr>
            );
          })}
        </tbody>
      </table></div>
      <p>The pre-registered rule flagged drift in both regions. After seeing the data we found Aqua&rsquo;s overpass had moved later, so test years where the two satellites no longer passed within {t2.parameters.match_tolerance_h} h of each other cannot be compared. The revised rule (D-034) keeps only evaluable years, and both verdicts are shown. {t2.control_note}.</p>

      <OverpassChart data={charts} region="IN_Punjab" title="Overpass time, Punjab (India)" windowLabel={win} />
      <OverpassChart data={charts} region="PK_Punjab" title="Overpass time, Punjab (Pakistan)" windowLabel={win} />
      <RatioChart data={charts} region="IN_Punjab" title="Aqua / S-NPP ratio vs timing gap, Punjab (India)" splitYear={splitYear} />
      <RatioChart data={charts} region="PK_Punjab" title="Aqua / S-NPP ratio vs timing gap, Punjab (Pakistan)" splitYear={splitYear} />

      <h2 id="t2b">T2b: night share of S-NPP detections</h2>
      <p>Claimed as consistency, not proof.</p>
      <div className="table-wrap" role="region" aria-label="T2b consistency checks (scrollable table)" tabIndex={0}><table data-testid="t2b-table">
        <thead><tr><th>Region</th><th>Mean {span(calib)}</th><th>Max {span(calib)}</th><th>Mean {span(test)}</th></tr></thead>
        <tbody>
          {[...regions, "rest_of_box"].map((r) => {
            const s = t2.t2b[r]?.night_share.SNPP ?? {};
            const a = meanShare(s, calib), m = maxShare(s, calib), b = meanShare(s, test);
            return <tr key={r}><td>{REGION_NAME[r]}</td><td className="num">{a === null ? "–" : fmtPct(a, 2)}</td><td className="num">{m === null ? "–" : fmtPct(m, 2)}</td><td className="num">{b === null ? "–" : fmtPct(b, 2)}</td></tr>;
          })}
        </tbody>
      </table></div>

      <h2 id="t3">T3: why did the ratio move? Orbit, timing or a real decline</h2>
      <p>Three explanations, each judged by rules written before any T3 number was computed (D-039). Pre {span(t3.parameters.pre_years)}, post {span(t3.parameters.post_years)}, window {t3Win}, {t3.window.time_basis}. The control region is a diagnostic for the method, not a finding.</p>
      <div className="table-wrap" role="region" aria-label="T3 evidence (scrollable table)" tabIndex={0}><table data-testid="t3-table">
        <thead><tr><th>Region</th><th>Explanation</th><th>Supporting</th><th>Against</th><th>Verdict</th></tr></thead>
        <tbody>
          {t3.regions.flatMap((r) => (["O", "T", "D"] as const).map((k) => {
            const ev = t3.t3[r]?.evidence[k];
            if (!ev) return null;
            return (
              <tr key={`${r}-${k}`}>
                <td>{REGION_NAME[r] ?? r}</td>
                <td>{EXPLANATION[k]}</td>
                <td><small>{ev.supporting.join("; ") || "none"}</small></td>
                <td><small>{ev.against.join("; ") || "none"}</small></td>
                <td><span className={`verdict ${t3VerdictClass(ev.verdict)}`}>{ev.verdict}</span></td>
              </tr>
            );
          }))}
        </tbody>
      </table></div>

      {(["IN_Punjab", "PK_Punjab"] as const).map((r) => t3.t3[r] && (
        <div key={r} data-testid={`t3-daynight-${r}`}>
          <DayNightChart data={t3.t3[r]} title={`VIIRS day and night detections, ${REGION_NAME[r]}`} windowLabel={t3Win} />
          <details className="chart-data">
            <summary>Table: day and night detections by year, {REGION_NAME[r]}</summary>
            <div className="table-wrap" role="region" aria-label={`Day and night detections, ${REGION_NAME[r]} (scrollable table)`} tabIndex={0}><table>
              <thead><tr><th>Year</th><th>S-NPP day</th><th>S-NPP night</th><th>S-NPP night share</th><th>NOAA-20 day</th><th>NOAA-20 night</th></tr></thead>
              <tbody>
                {Object.keys(t3.t3[r].a2_viirs_only.snpp).sort().map((y) => {
                  const a = t3.t3[r]!.a2_viirs_only.snpp[y]!, b = t3.t3[r]!.a2_viirs_only.noaa20[y];
                  return <tr key={y}><td>{y}</td><td className="num">{a.day.toLocaleString("en-GB")}</td><td className="num">{a.night.toLocaleString("en-GB")}</td><td className="num">{fmtPct(a.share, 2)}</td><td className="num">{b ? b.day.toLocaleString("en-GB") : "–"}</td><td className="num">{b ? b.night.toLocaleString("en-GB") : "–"}</td></tr>;
                })}
              </tbody>
            </table></div>
          </details>
        </div>
      ))}

      <N20RatioChart data={Object.fromEntries(t3.regions.filter((r) => t3.t3[r]).map((r) => [r, t3.t3[r]!]))} names={short} title="NOAA-20 / S-NPP ratio by year" />
      <details className="chart-data">
        <summary>Table: NOAA-20 / S-NPP ratio by year</summary>
        <div className="table-wrap" role="region" aria-label="NOAA-20 to S-NPP ratio (scrollable table)" tabIndex={0}><table data-testid="t3-ratio-table">
          <thead><tr><th>Year</th>{t3.regions.map((r) => <th key={r}>{REGION_NAME[r] ?? r}</th>)}</tr></thead>
          <tbody>
            {Object.keys(t3.t3[t3.regions[0]!]?.a1_noaa20_snpp.by_year ?? {}).sort().map((y) => (
              <tr key={y}><td>{y}</td>{t3.regions.map((r) => { const v = t3.t3[r]?.a1_noaa20_snpp.by_year[y]; return <td key={r} className="num">{v ? fmtNum(v.ratio, 3) : "–"}</td>; })}</tr>
            ))}
            <tr><td>Theil–Sen, per year (95% CI)</td>{t3.regions.map((r) => { const ts = t3.t3[r]?.a1_noaa20_snpp.theil_sen; return <td key={r} className="num">{ts ? `${fmtPct(ts.slope_pct_per_year, 1, true)} (${fmtPct(ts.ci95_pct_per_year[0], 1, true)} to ${fmtPct(ts.ci95_pct_per_year[1], 1, true)})` : "–"}</td>; })}</tr>
          </tbody>
        </table></div>
      </details>

      <h2 id="flags">Reliability flags in the calendar</h2>
      <p>T3 also flags calendar years where the harmonized record is less comparable. {t3.district_inheritance}. Custom boxes and circles take the flags of every calibration region they overlap.</p>
      <ul data-testid="t3-flags">
        {t3.regions.map((r) => {
          const rel = t3.t3[r];
          const caution = Object.entries(rel?.reliability ?? {}).filter(([, v]) => v.harmonization_reliable !== "yes");
          return (
            <li key={r}><strong>{REGION_NAME[r] ?? r}:</strong>{" "}
              {caution.length === 0 ? "no caution years." : caution.map(([y, v]) => `${y} (${v.reasons.map((c) => plainReason(c, t3.reason_codes)).join("; ")})`).join(", ")}
            </li>
          );
        })}
      </ul>

      <h2 id="mask">Mask report</h2>
      <p>The persistent-hotspot mask ({mask.parameters.rule} rule, {mask.n_masked_cells} cells) removes:</p>
      <div className="table-wrap" role="region" aria-label="Mask report (scrollable table)" tabIndex={0}><table data-testid="mask-table">
        <thead><tr><th>Platform</th><th>Detections</th><th>Removed</th><th>Share</th></tr></thead>
        <tbody>
          {Object.keys(mask.detections_total_by_platform).map((p) => (
            <tr key={p}><td>{p}</td><td className="num">{mask.detections_total_by_platform[p]!.toLocaleString("en-GB")}</td><td className="num">{(mask.detections_removed_by_platform[p] ?? 0).toLocaleString("en-GB")}</td><td className="num">{fmtPct(mask.share_removed_by_platform[p] ?? 0, 2)}</td></tr>
          ))}
        </tbody>
      </table></div>
    </main>
  );
}
