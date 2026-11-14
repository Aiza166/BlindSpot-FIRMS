// Plain-words text for the month-level critical-period panel (D-042). Numbers come from AreaDoc.critical.
import { fmtRatio } from "./format";
import type { CriticalDoc } from "./types";

export const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export function criticalSentence(c: CriticalDoc): string {
  if (c.peak === null || c.onset === null || c.end === null) return "No critical months: too few complete years to rank the months of the year.";
  const span = c.onset === c.end ? MONTH_NAMES[c.onset - 1]! : `${MONTH_NAMES[c.onset - 1]} to ${MONTH_NAMES[c.end - 1]}`;
  const more = c.other_months.length ? ` A second, smaller group of months: ${c.other_months.map((m) => MONTH_NAMES[m - 1]).join(", ")}.` : "";
  if (c.onset === c.end) return `Typically confined to ${span}: burning starts, peaks and ends within that month.${more}`;
  return `Typically starts in ${MONTH_NAMES[c.onset - 1]}, peaks in ${MONTH_NAMES[c.peak - 1]} and ends in ${MONTH_NAMES[c.end - 1]} (${span}).${more}`;
}

export function thisYearSentence(c: CriticalDoc, monthLabel: (ym: string) => string): string | null {
  const t = c.this_year;
  if (!t || t.value === null) return null;
  const rel = t.typical === null || t.ratio === null ? "no typical value for this month" : `${fmtRatio(t.ratio)}× the typical ${MONTH_NAMES[Number(t.month.slice(5, 7)) - 1]} (typical ${t.typical})`;
  return `${monthLabel(t.month)}: ${t.value}, ${rel}. ${t.in_critical ? "This month is a critical month." : "This month is not a critical month."}${t.year_flagged ? " The year is flagged, so read it with the caution notes." : ""}`;
}
