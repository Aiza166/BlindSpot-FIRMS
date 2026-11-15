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
- **Status:** Done 14 Nov (W5). The second team member asked for "the best version of W5" and Claude finalised the wording; the team can still edit the template.
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
- **Status:** Done 14 Nov (W2, agreed by Aiza). Run on the second team member's PC; results below under "Run, 14 Nov".
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

## W-13 · Shorter disclosure, no link to the earlier repository
- **Status:** Agreed by the second team member, 14 Nov ("yes, do these all"; asked that the submitted work not link back to the earlier repository).
- **Decision:** The README "Project history", the project page "What was built when" and `ai-log.md` now say in one or two sentences that the pipeline, its tests and a first app version were prepared locally before the event under the Local Lead's permission, and list what was built during the event. The earlier repository is no longer named in these files or in `HANDOFF.md`. Setup instructions (`YOUR_TASKS/03`, `YOUR_TASKS/04`, `docs/CONTINUE.md`) now point at `Aiza166/BlindSpot-FIRMS`. Out-of-date README lines were corrected: the Windows notes and the 1 Nov test summary (now the counts run on 14 Nov).
- **Why:** The disclosure was spread over several places and long. A short statement plus a "built during the hackathon" list shows the event work more clearly.
- **Kept:** The statement that work was prepared before the event stays in every place it was. Claude declined to change dates so that the earlier work appears to start on 14 Nov (W-01 still applies). Historical records (`docs/DECISIONS.md`, `docs/CHECKPOINTS.md`, `docs/chat/`) keep their real dates.
- **Rejected:** Removing the disclosure or re-dating earlier work.
- **Run, 14 Nov:** FIRMS availability on the day was the same as recorded above. The six sources were downloaded again with the same commands (43, 43, 49, 22, 22, 15 files; 357,763 rows). The extension read 357,763 rows, kept 262,737 after the filters and 259,477 after the frozen mask, and updated 350 area files. Provisional from 2026-08 (S-NPP, NOAA-20) and 2026-09 (Aqua, Terra). The app record now ends 2026-10.
- **Bug found and fixed in the run:** the first run recomputed the 2003–2025 median excluding flagged years, and the critical-period threshold, from the rounded values stored in the app files. The last digit moved in 88 areas (for example 12.7 to 12.8) and the threshold in 9. The extension now keeps the stored baseline and moves only the "this year" line, read against the stored median. A new test (`test_stored_baseline_is_kept_not_recomputed_from_rounded_values`) failed before the fix and passes after it. After the re-run, a check against git found no change in any 2003–2025 value, median, median excluding flagged years, or critical-period field in the 350 areas; calibration factors are identical; the only changed old `days_available` entry is January 2026 (1 day before, 31 now: the old data held only 1 January).
- **Month-card wording:** "Near-real-time data is not part of this build, so this card shows the cached archive snapshot" was no longer true, because the saved data now hold near-real-time months. It now says the live service is not part of this build and the card shows the latest month in the saved data. The browser check for that text was updated to match.
- **Checked by hand in the app:** Punjab (Pakistan), Punjab (India) and Sangrur show a 2026 row; August to October 2026 have a dashed outline and "provisional" in their labels; 2026 carries the "not tested" caution; the card reads "October 2026 · provisional".
- **Known display detail, not changed:** for very small ratios the card's two lines can differ in the second digit (Sangrur: 0.0075× from the median line, 0.0070× from the stored "this year" ratio, which the pipeline rounds to 3 decimals).
- **Sanity check of the low Indian Punjab October 2026 value (0.041× its median):** NOAA-20 alone agrees (1,317 against S-NPP 1,111), and October S-NPP counts fell each year from 14,581 (2022) to 6,890, 2,289, 1,439 (2025) and 1,111 (2026).
- **Browser tests, 14 Nov (second PC):** first run 12 of 14 checks then an exception. Both failures came from the record now ending in October: Ctrl+End landed on December 2026, an "outside the archive" cell; and a check looked for November of the last caution year, which is now 2026 ("not tested"). Fixes: Ctrl+End now moves to the last month of the record (`web/components/Calendar.tsx`, an app fix for keyboard users); the check now picks the last year flagged for the Aqua drift reason, which is what it tests (`web/e2e/run.mjs`). After the fixes: 192 of 192. No threshold, window, region, factor or science test changed.
- **Project page regenerated:** the only changes are "2003–2025" to "2003–2026" in two places of `docs/SUBMISSION.md` and the matching row in `docs/SUBMISSION_SOURCES.md`; the video script, morning summary and subtitles render unchanged. `make story` could not run as is: the custom-area check (`web/e2e/check_custom_aoi.py`) needs `data/processed/harmonized/calibration_factors.parquet`, a full-pipeline output that is not in git and not on this PC. The page was rendered with `story.render` outside the repository, using the three custom-area values from the last real run (83 months compared, 1 differing, max 4.7%, recorded in `docs/SUBMISSION_SOURCES.md`); that check reads only pre-2012 Aqua tiles, which W2 did not touch, and the rendered custom-area lines match the committed page exactly. The check itself was not re-run. `story.py` now writes paths with forward slashes, so Windows and Linux give the same file.
- **Seen, then fixed 15 Nov:** the caution banner ran two different reasons together when 2026 and the drift years were both in view; it now names the years before each reason when there is more than one. The empty-cell legend entry now reads "No data (platform not flying, no factor, or month not yet in the archive)", which covers November and December 2026. Browser suite 192 of 192 after the change.

## W-14 · Project page rewrite (W5) and the other-regions paragraph (W6)
- **Status:** Done 14 Nov. Asked for by the second team member; wording not yet read aloud by a team member.
- **Decision:** `docs/templates/SUBMISSION.tmpl.md` now opens on a district officer and the 2012 jump; summary 148 words, detailed description 531 words (it includes the tools list and the pre-event disclosure the form needs), down from about 2,700 words for the page. The long test tables, the brief-mapping table and the extra T3 checks moved off the page; the page points to the app's Results page and `docs/RESULTS_T1.md` to `docs/RESULTS_T3.md`. An "Other regions" section (W6) says the method uses only global FIRMS inputs and that a new region needs its own calibration and the same three tests. NASA data, references, partner data and SI sections are unchanged.
- **Kept:** every number is a placeholder read from the results files; the limits stay (Indian Punjab fails after 2021, later and less burning cannot be separated, Pakistani Punjab untested, the T2 rule change, counts are an index).
- **Generator and tests:** a `month` format (2026-10 to "October 2026") with a test; the lead-sentence test now expects the person-first opening; the number-tracing test now strips image and link targets and licence identifiers (BSD-3-Clause, Apache-2.0), which had passed before only because a placeholder happened to print the same digits. Neither change lets a hand-typed result number through.
- **Rendering:** as for W2, `make story` could not run here because the custom-area check needs a full-pipeline file not on this PC; the page was rendered with the same code and the custom-area values from the last real run. The video script, morning summary and subtitles render unchanged.
- **Not on the app's Results page:** the factor-spread, Terra/Aqua before 2012 and orbit-model checks; they are in `docs/RESULTS_T3.md`.
- **Rejected:** opening on a statistic; dropping the limits; a second region.

## W-15 · Team, event and deadline
- **Status:** Recorded 15 Nov from the second team member's answers and the Space Apps site.
- **Facts:** Team name "Hehehehehe" (team page https://www.spaceappschallenge.org/2026/find-a-team/hehehehehe/, read 15 Nov: Local Event Karachi, Pakistan; challenge Harmonization of MODIS and VIIRS Hot Spots; the About text describes Blind Spot). The team member reports that both members are on this team at the Karachi Local Event and that the Team Owner is a team member. The member list itself was not visible without signing in.
- **Deadline:** the 2026 Project Submission Guide (read 15 Nov) says submission closes Sunday 15 November at 11:59 p.m. in the time zone of the team's Local Event, so **23:59 PKT on 15 Nov 2026**. The Universal Event rule (Team Owner's time) does not apply. Local judging and awards times may differ; the guide says to check with the Local Lead.
- **Old repository:** the team will make `Aiza166/nasa-hackathon` private before the final submission.
- **Changed:** deadline lines in `README.md`, `docs/WEEKEND_PLAN.md` and `YOUR_TASKS/10_submit_form.md`.

## W-16 · Video script: names and team name first, a "future" line last
- **Status:** Done 15 Nov (W9 preparation). Asked for by the second team member; not yet read aloud.
- **Decision:** The voice-over opens "Aiza and Kissa, team Hehehehehe." and ends "Next: any farming region, same tests.", following the 2026 guide's order (names and team name at 0:00, the future at 0:20–0:30). The first shot is the app's new first screen (the 2012 story strip and the Harmonize button), with the calendar now to 2026. 54 words, under the 55-word cap; subtitles regenerated (5 cues, 0 to 30 s). The caveat line is unchanged.
- **Tests:** the subtitle test now expects the team-name cue first and the 2012 jump second; "18" (the under-18 rule) joins the allowed fixed numbers.
- **Not done:** recording, the 30.0 s check with `ffprobe`, upload. The end card shows the public link if the site is deployed in time, otherwise the GitHub link.

## W-17 · Deploy to Cloudflare Pages (W10) and the live current month (W3)
- **Status:** Done 15 Nov. Production URL: https://blindspot-firms.pages.dev (project `blindspot-firms`; `blindspot` was taken).
- **How:** a team member logged Wrangler in and set `FIRMS_MAP_KEY` as an encrypted Pages secret; Claude created the project, built `web/out` with `NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt`, checked that no key characters are in the output, and uploaded it with `wrangler pages deploy` (Direct Upload, D-041).
- **Two problems found and fixed:**
  - The first secret was saved under a 32-character name instead of `FIRMS_MAP_KEY` (the key was most likely entered as the name). Claude deleted it on the team member's request and the member set it again; the list now shows only `FIRMS_MAP_KEY`. Advice given: request a new FIRMS key after the hackathon, since the name was visible in the Cloudflare settings and in one tool output.
  - Git Bash rewrote `/api/nrt` into a Windows path at build time, so the first deploy's card could not reach the function (CSP blocked it). Rebuilt with `MSYS_NO_PATHCONV=1`; `docs/DEPLOY.md` now warns about it.
- **Checked on the public URL, 15 Nov:** home, results, use-case, methods, about and attribution return 200; security headers present (CSP, nosniff, referrer policy, permissions policy, X-Frame-Options DENY, HSTS); `/api/nrt` returns `status: ok`, `provisional: true`, November 2026, 15 of 30 days, for Sangrur (297 NOAA-20 detections) and Pakistani Punjab (4,817); another origin gets 403 and a box outside the coverage area 400; the first 8 key characters appear in none of the served pages, the main script or the function response; a fresh browser tab shows no console errors; the live card reads "NOAA-20 VIIRS, November 2026 · near-real-time, provisional".
- **App change:** the card's "appears here when the near-real-time service is switched on at launch" note is now hidden once the live figure has loaded. Browser suite 192 of 192 (on the build without the live service, which the suite expects).
- **Project page and video script:** now give the live URL; the page says the current month comes in live and is labelled provisional.
- **Not checked yet:** a phone over mobile data, and a drawn custom area on the public URL.


## W-18 · Live month: one slow FIRMS call no longer fails the card (FIXES_FOR_KISSA item 1)
- **Problem:** Aiza saw `/api/nrt` answer 504 "FIRMS did not answer in time" after 10.1 s (about 19:30 PKT, 15 Nov). The card then fell back to October, while the project page says the current month comes in live.
- **Cause, measured before any change (about 19:45–19:55 PKT):** the key is fine (356 of 5,000 transactions in the 10-minute window; every call returned CSV). FIRMS answer times vary: 16 direct calls took 1.6–2.9 s, except 6.7 s, 7.0 s and 9.1 s. The function fetched the month's 5-day windows one after another (4 on 15 Nov) with a 10 s limit per call and no retry, so one call over 10 s failed the whole answer. 17 uncached public requests in the same window all returned 200 (2.0–12.3 s), so the failure comes and goes. The Cloudflare log stream (`wrangler pages deployment tail`) did not connect from this PC, so no server-side log of a failed call was captured.
- **Decision:** in `functions/_lib/nrt-core.ts`, fetch the windows up to 4 at a time (`FIRMS_PARALLEL`; Workers allow 6 open connections per request), raise the per-call limit to 20 s, retry a timed-out call once, and cut every call off at the unchanged 25 s overall budget. Results keep window order; counting, filters, mask and cache are unchanged.
- **Rejected:** only raising the timeout (4 slow calls one after another would still exceed the budget); changing the wording to "when NASA's service answers" (kept as the fallback if this had not been ready in time).
- **Tests first:** 4 new tests in `web/functions/nrt.test.ts` failed on the old code (parallel requests, at most 4 open, retry after one timeout, the 20 s / 25 s constants), plus one that the retry never passes the budget. Then: NRT tests 29 of 29, web unit tests, lint and types, Python lint and tests, browser suite 192 of 192. `web/e2e/check_custom_aoi.py` could not run here (needs `calibration_factors.parquet`, only on Aiza's PC).
- **Deployed 15 Nov, about 20:15 PKT** (deployment `1614c9eb`, build with `MSYS_NO_PATHCONV=1`, no "Program Files" path and no key characters in `out/`). On the public URL: 10 uncached areas all returned 200 in 0.8–5.9 s (before the change: 2.0–12.3 s); Sangrur 200, 319 detections, 15 of 30 days; another origin 403; a box outside the coverage area 400; all six pages 200.

## W-19 · Month card text while loading and after launch (FIXES_FOR_KISSA item 2)
- **Problem:** on the public site, while the live request was still running, the card said "The live near-real-time service is not part of this build", which is wrong there; and when the live request failed it added "appears here when the near-real-time service is switched on at launch", although the site has launched.
- **Decision:** the card's note comes from `web/lib/cardNote.ts`. On a build with `NEXT_PUBLIC_NRT_ENDPOINT` set: "Loading the live current month…" while the request runs, the live-figure sentence once it loads, "Near-real-time data could not be loaded (reason), so this card shows the latest month in the saved data." if it fails, and never the launch note. On a build without the endpoint (local and test builds) the text is unchanged, so the browser checks that read it still apply.
- **Rejected:** removing the launch note everywhere (it is still true for a build without the service).
- **Tests first:** `web/lib/cardNote.test.ts` (5 tests) failed before the module existed. Then: web unit tests 52 of 52, lint and types clean, Python lint and tests, browser suite 192 of 192 (build without the endpoint).
- **Deployed 15 Nov** (deployment `8d94770e`; no "Program Files" path, no key characters in `out/`). Checked in a browser on the public URL: Sangrur shows the live card (319, 15 of 30 days) and the live-figure note; switching to Bahawalnagar showed "Loading the live current month…" and then the live figure (234, 15 of 30 days); the launch note did not appear; no console errors.
