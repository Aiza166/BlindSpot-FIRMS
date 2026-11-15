// Foot notes of the month card (FIXES_FOR_KISSA item 2, decisions.md W-19). `nrt` is null while
// the live request is still running; `hasService` is true when the build sets NEXT_PUBLIC_NRT_ENDPOINT.
import type { NrtResult } from "./nrt";

const NO_SERVICE = "The live near-real-time service is not part of this build, so this card shows the latest month in the saved data.";

export function cardFootNote(nrt: NrtResult | null, hasService: boolean): string {
  if (!hasService) return NO_SERVICE;
  if (nrt === null) return "Loading the live current month…";
  if (nrt.status === "ok") return `The ${nrt.data.label} figure is FIRMS ${nrt.data.source}, filtered and masked like the archive, and will change when the standard data replace it.`;
  return `Near-real-time data could not be loaded (${nrt.reason}), so this card shows the latest month in the saved data.`;
}

/** "Appears here when ... switched on at launch" only makes sense on a build without the service. */
export function showLaunchNote(hasService: boolean): boolean {
  return !hasService;
}
