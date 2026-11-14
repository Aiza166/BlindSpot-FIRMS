# Decisions (hackathon weekend, from 14 Nov 2026)

Each entry: what was decided, why, what was rejected, and who decided. Earlier decisions (D-001 to D-048, 31 Oct to 14 Nov) are in `docs/DECISIONS.md`.

Status: **Proposed** = Claude's recommendation, waiting for the team. **Agreed** = a team member said yes.

## W-01 · Say plainly what was built before the hackathon
- **Status:** Agreed by Aiza, 14 Nov ("yes, disclose it").
- **Decision:** Wherever the code lives, the project page, README and `ai-log.md` state that the pipeline and app were prepared on 31 Oct to 2 Nov, and list what was built during the event.
- **Why:** The Participant FAQ says teams may not begin work before the hackathon. The submission form asks the team to confirm the rules were followed. A new repository changes where the code is stored, not when it was written. If the history is hidden and a judge or organiser finds out, the likely result is disqualification; if it is disclosed with the Local Lead's written permission, the team has an answer.
- **Rejected:** Presenting the existing code as work that started on 14 Nov. Claude will not write a log, commit history or page text that says so.
- **Done 14 Nov:** "Project history" in `README.md`, "What was built when" in `docs/SUBMISSION.md`, and the first section of `ai-log.md`.
- **Open:** the Local Lead's written reply.

## W-02 · New repository
- **Status:** Agreed by Aiza, 14 Nov. Repository: `Aiza166/BlindSpot-FIRMS`.
- **Decision:** The new repository is the public home for the weekend's work. Its first commit says it imports the code prepared earlier, and W-01 applies. The two chat-export scripts were changed in the import so they no longer contain the first 8 characters of a third-party key; the rule now redacts any 32-character hex string. Personal email addresses were removed from the two chat exports in `docs/chat/` (22 places).
- **Why:** It also drops the old history that contains the first 8 characters of a third-party key (`docs/QA_REPORT_FINAL.md`, Q-3).
- **Rejected:** A first commit that reads as a fresh start.

## W-03 · Fix the "month-by-day" wording; do not build a daily calendar
- **Status:** Agreed by Aiza, 14 Nov. Done 14 Nov in the README, the submission and its template.
- **Decision:** Change the README, submission and app text to say what the calendar shows: one cell per month, one row per year.
- **Why:** The official brief asks for colour ramps "across months". The app already does that. The error is in our description.
- **Rejected:** Building a daily view this weekend (not asked for, and it costs hours needed elsewhere).

## W-04 · Add 2026 to date from the FIRMS area API, marked provisional
- **Status:** Proposed. Needs a FIRMS MAP_KEY.
- **Decision:** Fetch January to November 2026 for the coverage box and show it as a 2026 row, labelled provisional. Keep it out of calibration, and out of medians unless the month is complete.
- **Why:** The brief says "from the early 2000s to the present". The app's data ends in December 2025; the 2026 tiles hold only 61 detections dated 1 January.
- **Rejected:** Leaving the record at 2025 and relying on the live card alone (ten months of 2026 would still be missing).
- **Rules kept:** `CLAUDE.md` scientific rules 3, 5 and 8.

## W-05 · No second region this weekend
- **Status:** Proposed.
- **Decision:** Keep Punjab. Add one paragraph on how the method extends to other regions.
- **Why:** A new region needs its own download, calibration and tests, and the pipeline has never run on this PC. Untested factors would weaken the strongest part of the project.
- **Rejected:** A quick extra region to look global.

## W-06 · Rewrite the project page for a reader with no background
- **Status:** Proposed.
- **Decision:** A summary of about 150 words that opens with a person and a problem, and a page of about 600 words. Test details move to the app's Results page.
- **Why:** The four 2025 winning pages we read are short and open with a human problem. Ours is about 2,700 words and opens with a statistic.
- **Rejected:** Cutting the limits and the failed test from the page. They stay, in two or three plain sentences.

## W-07 · Open the app on the 2012 story
- **Status:** Agreed by Aiza, 14 Nov. Done 14 Nov.
- **How it was built:** With no deep link, the Explorer opens on the Punjab (Pakistan) region in the raw view, with a strip above the month card: "Start here: the 2012 jump" and a button "Harmonize the record". The strip's numbers and dates come from `results/t1.json`. Picking any area ends the story and returns to the harmonized view. A `?area=` deep link shows no story.
- **Kept from D-044 and D-046:** the month card stays before the calendar and stays above the fold on a 390 × 844 phone, so the calendar itself is still below the first screen. The strip tells the visitor what the calendar shows and scrolls to it on click.
- **Rejected while building:** moving the calendar above the month card (breaks the "answer first" order agreed in D-044 and its phone test); a longer strip (pushed the phone answer to 909 px of 844).
- **Test change:** the touch-drawing check now starts from a district deep link, because a finger drag across the region-wide map selects more detections than the browser limit.
- **Evidence:** 7 new unit tests (42 of 42 pass); 7 new browser checks (192 of 192 pass on this PC).
- **Decision:** The first screen shows Pakistani Punjab in the raw view with the 2012 jump, and one button to harmonize.
- **Why:** The first screen now shows a quiet December 2025 card. A judge gives a project a few minutes.
- **Rejected:** Keeping the current default and relying on the video to tell the story.

## W-08 · Do not chase a higher Validity score with a new check
- **Status:** Proposed.
- **Decision:** No new independent validation this weekend. Present the after-2021 failure as what it is: the app tells the user when not to trust the number.
- **Why:** A rushed comparison against outside figures risks a wrong number on the page.

## W-09 · Task split
- **Status:** Proposed.
- **Decision:** Aiza: eligibility email, team and event check, FIRMS key, Cloudflare deploy, number checks, the form. Kissa: page edit, outreach, video recording. Claude Code: code and first drafts, reviewed by a team member before each commit. Full table in `docs/WEEKEND_PLAN.md`.
- **Why:** Account, key, voice and submission steps can only be done by a person; the two members can work in parallel.

## W-10 · Critical-period sentence for a single month
- **Status:** Done 14 Nov (part of W4, agreed by Aiza).
- **Decision:** When onset, peak and end are the same month, the card says "Typically confined to May: burning starts, peaks and ends within that month." Periods that span several months keep the old sentence.
- **Why:** The old text read "starts in May, peaks in May and ends in May (May)".
- **Rejected:** Rewording the multi-month sentence as well (it reads correctly, and browser tests may depend on it).
- **Evidence:** two new unit tests in `web/lib/critical.test.ts`, written first and seen failing; 35 of 35 unit tests pass; the sentence was read in the built app for Amritsar.

## W-11 · Browser tests are not run on this PC yet
- **Status:** Closed 14 Nov. Playwright was installed locally with `npm install --no-save playwright` and `npx playwright install chromium` because W7 changes the first screen and could not be checked without it. `package.json` is unchanged. Baseline before W7: 185 of 185 on Windows.
- **Decision:** `web/e2e/run.mjs` needs Playwright, which is not in `web/package.json` and is not installed here. It was not installed without asking, because it downloads a browser (about 150 MB).
- **Effect:** On this PC the checks are the build, lint, type check, 35 unit tests and 186 Python tests. The 185 browser checks last ran on 2 Nov on Linux.

## W-12 · Add 2026 to the record without re-running 2003–2025
- **Status:** In progress 14 Nov (W2, agreed by Aiza).
- **Facts checked 14 Nov** (FIRMS data-availability API): standard (SP) data run to 31 Jul 2026 for VIIRS and 31 Aug 2026 for MODIS; near-real-time (NRT) data cover 1 Aug–2 Nov 2026 for S-NPP, 1 Aug–14 Nov for NOAA-20, 1 Sep–14 Nov for MODIS.
- **Decision:** A new step, `pipeline/blindspot/extend.py`, appends 2026 to the existing app data. It downloads the coverage box from the FIRMS area API, applies the same filters, and reuses `calibrate.monthly_sql`, `calibrate.harmonize`, `calibrate.raw_series`, `regions.assign_points` and `appdata.critical_periods`, so the counting and the splice are the pipeline's own code.
- **Frozen (not refit, not changed):** the persistent-hotspot mask (the cells in `web/public/data/nrt/mask_cells.json`, which the NRT function already uses), the calibration factors, the 2003–2025 medians, and T1–T3. A test checks that the medians do not move.
- **Months:**
  - Jan–Jul 2026: S-NPP standard data, the same as history.
  - Aug–Oct 2026: S-NPP near-real-time. Marked **provisional** in the calendar (dashed outline), the tooltip, the month card and the CSV (rule 8).
  - November 2026: S-NPP NRT stops on 2 Nov, and the existing splice switches to NOAA-20 × factor from 2026-11 (PLAN §4, `calibrate.SNPP_LAST_MONTH`). November is incomplete, so the calendar ends at October; November appears only on the live card.
- **Flags:** 2026 is marked as a caution year with a new reason, "not tested": the tests were run before this year existed.
- **Two rules adapted for NRT data, and why:**
  - NRT rows have no `type` field, so they get confidence, coverage box and mask, but no type filter. This is the rule the NRT function already uses (D-010).
  - Days available (D-026) count any in-box row, not only standard rows, because the standard archive stops in July.
- **Rejected:**
  - Re-running the whole pipeline with 2026. The mask is fit on all years, so new data could move every historical number; the run also takes about two hours and was never tested on Windows.
  - Showing November 2026 in the calendar as a partial month.
- **Boundaries:** geoBoundaries were downloaded again on 14 Nov. All 347 district IDs match the app's.
- **Tests:** 9 new tests in `tests/test_extend.py`. They were written alongside the code, not run failing first.
