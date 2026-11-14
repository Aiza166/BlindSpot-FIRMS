// First-screen story (weekend decision W-07): open on the raw record of one calibration region so the
// 2012 sensor jump is the first thing a visitor sees, with one button to harmonize it.
// Every number comes from results/t1.json (CLAUDE.md rule 7); nothing is typed here.
import { MONTH_NAMES } from "./critical";
import { fmtPct } from "./format";
import type { T1 } from "./results";

export const STORY_REGION = "PK_Punjab";

export interface Story { region: string; year: number; window: string; raw: string; harmonized: string }

/** "10-15" → "15 October". */
function dayMonth(md: string): string {
  const [m, d] = md.split("-").map(Number);
  return `${d} ${MONTH_NAMES[(m ?? 1) - 1]}`;
}

export function storyFromT1(t1: T1, region: string = STORY_REGION): Story | null {
  const s = Object.hasOwn(t1.results.hotspots, region) ? t1.results.hotspots[region]?.step_2012 : undefined;
  if (!s) return null;
  return {
    region,
    year: t1.parameters.step_year,
    window: `${dayMonth(t1.window.start)} to ${dayMonth(t1.window.end)}`,
    raw: fmtPct(s.raw_step, 0, true),
    harmonized: fmtPct(s.harmonized_step, 1, true),
  };
}

interface LandingIndex { regions: Record<string, string>; districts: { id: string; name: string }[] }

/** Which area the Explorer opens on. A valid ?area=<district id> deep link wins; otherwise the story region. */
export function landing(index: LandingIndex, areaParam: string | null): { id: string; story: boolean } | null {
  const linked = areaParam ? index.districts.find((d) => d.id === areaParam) : undefined;
  if (linked) return { id: linked.id, story: false };
  if (Object.hasOwn(index.regions, STORY_REGION)) return { id: STORY_REGION, story: true };
  const first = index.districts.find((d) => d.name === "Amritsar") ?? index.districts[0];
  return first ? { id: first.id, story: false } : null;
}
