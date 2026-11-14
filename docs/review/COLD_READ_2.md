# Cold read 2 (judge, SUBMISSION.md + VIDEO_SCRIPT.md only)

## Scores
- **Impact 3/5**: real users named (district officer, air-quality teams), but coverage is one 20x14 degree box, no live/NRT data, and no evidence any responder has seen it.
- **Creativity 4/5**: a harmonization that reports where it stops working (per-region-year flags, T3 O/T/D attribution, NOAA-20 cross-check) is genuinely beyond "multiply by a ratio".
- **Validity 4/5**: pre-registered tests, held-out years, bootstrap, honest fail on Indian Punjab; docked for a post-hoc T2 rule change, one regional factor for every district, and no independent check (MCD64A1, official counts).
- **Relevance 3/5**: calendar, median compare and CSV are covered; "accessible color ramps" is never mentioned; "selected area" works only inside Punjab/NW India; scientists are served better than emergency responders.
- **Presentation 2/5**: demo and app links are both TBD; the submission is padded with ~80 rows of internal placeholder keys and build notes; the T1/T2 table is hard to parse; the video has {NAMES} unfilled and crams 25 words into 10 s.

## Unclear
- "+613% though nothing changed on the ground": +613% over what baseline (2011 vs 2012 window counts? annual?). Not defined anywhere.
- Pakistani T1 label "pass (2012 step only; held-out not judged because T2 is inconclusive)" reads as half a pass; a judge cannot tell if the method works there after 2021.
- Why S-NPP as the reference instead of NOAA-20, and what the harmonized series does after S-NPP ends.
- How "usual level" is defined in the app (median of all years? excluding flagged years?) and whether flagged years enter the Sangrur median of 4,617.
- What a user sees for a district on a region border, and what "caution" actually changes in the app (greyed? excluded from median?).
- Video shot 3 says "less comparable" without saying what the viewer should do with that.

## Overclaimed
- "nothing changed on the ground" in 2012: asserted, not shown.
- "We fixed our tests before running them" in the summary, while the T2 rule was changed after data; leading with it invites suspicion.
- "The method should transfer to other regions" appears twice (and on the video end card) with zero tests outside Punjab.
- "Every number ... comes from the pipeline" is a process claim, not validity.
- "Researchers get a tested correction factor" when the test fails in one of two regions post-2021.
- Video "+13%" vs submission "+12.7%" and Pakistan-only figure presented as "Punjab's" record.

## Missing
- Working public app URL and video link (the single biggest gap).
- Accessible / colour-blind-safe colour ramp: explicitly required, never stated (name the palette, contrast checks).
- Screenshots inline (only file paths given; judges will not open repo paths).
- Team names, roles, and any user feedback from an actual responder or land manager.
- Independent validation (MCD64A1 burned area, PPCB/CAQM stubble-fire counts).
- Explicit "critical periods" output (e.g. peak-week window, onset date) rather than only a monthly ratio.
- Uncertainty shown to the user (factor intervals in the calendar/CSV?).

## Top 7 fixes, ranked by expected score gain
1. **Ship the live app URL and the 30 s video link** (Presentation +1 to +2, Impact +0.5). Without them judges cannot verify anything.
2. **Delete the "Number sources" tables and template/build notes from the submission** (move to repo); add 2-3 inline screenshots with captions (Presentation +1).
3. **State the accessible colour ramp explicitly** (palette name, CVD simulation, contrast ratio, non-colour encoding of flags) and show it in a screenshot (Relevance +1).
4. **Rewrite the results table as plain verdicts**: "2012 jump removed: yes/yes. Trustworthy after 2021: unknown/no (from 2022)". Put the T1/T2 mechanics below (Presentation +0.5, Validity clarity +0.5).
5. **Add one independent check** (MCD64A1 or official stubble-fire counts for Indian Punjab, even a single correlation) (Validity +1).
6. **Add a "critical period" output for responders**: typical onset/peak/end weeks per district and whether this year is early/late, plus define "usual level" and how flagged years are treated (Relevance +0.5, Impact +0.5).
7. **Cut overclaims**: drop "nothing changed on the ground" or support it, move "fixed in advance" next to the disclosed rule change, remove "should transfer" from the video end card, use +12.7% consistently, fill {NAMES}, and trim video shot 3 to <=18 words (Validity +0.5, Presentation +0.5).

## Resolution

Scores before: Impact 3, Creativity 4, Validity 4, Relevance 3, Presentation 2.
Scores after (COLD_READ_3, blind): Impact 4, Creativity 4, Validity 5, Relevance 4, Presentation 4.

Fixed in templates and story.py:
- The number-source tables moved to docs/SUBMISSION_SOURCES.md. story.py writes that file and tests/test_story.py still checks every value against it.
- Four screenshots are inline with alt text. The demo and app links are one line ("Live link added 14 Nov ...").
- A "How it meets the brief" table covers AOI, date range, calendar, month vs median, cividis with non-colour flags and the axe result read from axe-after.json, CSV and PNG.
- Overclaims cut. The 2012 jump is now defined (same fields, same days, S-NPP vs Aqua) and stated as coinciding with the sensor switch. The process line now discloses the T2 rule change. "Should transfer" became "uses only global FIRMS inputs; we tested only Punjab". The harmonized step uses one formatter (+12.7%) in both video and submission.
- Video shot 3 is 14 words. {NAMES} is listed under "What needs you" in MORNING_SUMMARY.
- New limitation: no independent check against non-FIRMS data yet. MCD64A1 was rejected as circular and too coarse (D-008).
