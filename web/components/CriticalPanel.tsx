import { criticalSentence, MONTH_NAMES, thisYearSentence } from "@/lib/critical";
import { fmtCount } from "@/lib/format";
import { ymLabel } from "@/lib/months";
import type { AreaDoc } from "@/lib/types";
import type { CustomDoc } from "@/lib/series";

/** Month-level critical period of the area (D-042). Words first; the table repeats it without colour. */
export function CriticalPanel({ doc }: { doc: AreaDoc | CustomDoc }) {
  const c = "critical" in doc ? doc.critical : undefined;
  const ex = "median_excl_flagged" in doc ? doc.median_excl_flagged : undefined;
  if (!c || !ex) {
    return (
      <section className="card" data-testid="critical-panel" aria-labelledby="crit-h">
        <h2 id="crit-h">Critical period</h2>
        <p className="foot">No critical period could be computed for this area.</p>
      </section>
    );
  }
  const drawn = !("level" in doc);
  const now = thisYearSentence(c, ymLabel);
  return (
    <section className="card" data-testid="critical-panel" aria-labelledby="crit-h">
      <h2 id="crit-h">Critical period<span className="tag">Month level, not daily</span></h2>
      <p data-testid="critical-sentence">{criticalSentence(c)}</p>
      {now && <p data-testid="critical-now"><strong>This year vs typical.</strong> {now}</p>}
      <p className="foot">
        Critical months are the months whose typical level is in the top quarter of the year (at or above {fmtCount(c.threshold)} hotspots), using {c.baseline_years[0]}–{c.baseline_years[1]}
        {c.excluded_years.length ? ` without the years we flag (${c.excluded_years.join(", ")})` : ""}. The data are monthly, so onset, peak and end are months, not days or weeks.
        {drawn ? " For a drawn area this is computed in your browser from its own series; the years we flag are those of every calibration region the area overlaps." : ""}
      </p>
      <details>
        <summary>Typical level by month</summary>
        <div className="table-wrap" role="region" aria-label="Typical level by month (scrollable table)" tabIndex={0}>
          <table data-testid="critical-table">
            <caption className="sr-only">Typical harmonized hotspots per calendar month, years we flag left out</caption>
            <thead><tr><th scope="col">Month</th><th scope="col">Typical hotspots</th><th scope="col">Critical month</th></tr></thead>
            <tbody>
              {MONTH_NAMES.map((n, i) => (
                <tr key={n}>
                  <th scope="row">{n}{c.peak === i + 1 ? " (peak)" : c.onset === i + 1 ? " (onset)" : c.end === i + 1 ? " (end)" : ""}</th>
                  <td className="num">{fmtCount(ex.values[i] ?? null)}</td>
                  <td>{c.months.includes(i + 1) ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
