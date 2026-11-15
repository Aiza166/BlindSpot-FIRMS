# Handoff, 15 Nov 2026: what the second team member's session did

For Aiza. Written by Claude Code at the end of the work on Kissa's PC. Every change below is also in `ai-log.md` (one row per piece of work) and `decisions.md` (W-13 to W-17, with reasons). Nothing here is a plan; it is what was done and checked.

**Deadline: tonight, Sun 15 Nov, 23:59 Karachi time (PKT).** The team "Hehehehehe" is on the Karachi Local Event (checked on the Space Apps site, `decisions.md` W-15).

## Links

- Live app: https://blindspot-firms.pages.dev
- Code: https://github.com/Aiza166/BlindSpot-FIRMS (`main` now holds all the weekend work; `weekend/w1-w4` is the same)
- Team page: https://www.spaceappschallenge.org/2026/find-a-team/hehehehehe/

## What was done (in order)

| # | Task | Result | Decision |
|---|---|---|---|
| 1 | Set up and checked on the second PC | Python 195 passed / 7 skipped, web lint, types, 42 unit tests and build all pass; boundaries downloaded, all 347 district IDs match | — |
| 2 | Disclosure text | README "Project history", the project page and `ai-log.md` now state it in one or two sentences, without naming the old repository, plus a "built during the hackathon" list; setup instructions point at the new repo | W-13 |
| 3 | **W2: 2026 added** | Record now runs to **October 2026**; August–October are near-real-time, outlined and labelled provisional; 2026 flagged "not tested". 357,763 rows downloaded with the same commands as on 14 Nov | W-12 |
| 4 | Bug found in W2 and fixed | The first run moved the last digit of a stored 2003–2025 median in 88 areas. Fixed with a failing test first; after the re-run no 2003–2025 value, median or critical period changed in any of the 350 areas (checked against git) | W-12 |
| 5 | Browser tests | Playwright installed locally (not in `package.json`); 192 of 192 pass. Two fixes: Ctrl+End stops on the last real month; one check now tests the year it means to | W-12 |
| 6 | **W5 + W6: project page rewritten** | Opens on a district officer and the 2012 jump; 148-word summary; description about 530 words (was about 2,700 in total); "Other regions" paragraph; every number still read from the results files | W-14 |
| 7 | Team, event, deadline recorded | Deadline lines in README, weekend plan and the form guide now say 23:59 PKT, Karachi Local Event | W-15 |
| 8 | `main` updated | Fast-forward merge of `weekend/w1-w4` into `main`, pushed; no history rewritten | — |
| 9 | **Video script ready (W9 prep)** | Opens "Aiza and Kissa, team Hehehehehe", ends "Next: any farming region, same tests"; 54 words; English subtitles regenerated (`docs/video/subtitles.srt`) | W-16 |
| 10 | Two display fixes | Caution banner names the years before each reason; the empty-cell legend also covers months not yet in the archive | W-12 |
| 11 | **W10 + W3: deployed, live month working** | https://blindspot-firms.pages.dev; live card "NOAA-20 VIIRS, November 2026 · near-real-time, provisional"; all pages 200; security headers present; key appears nowhere on the site | W-17 |
| 12 | Phone check on mobile data | Kissa ran the full checklist on a phone (private tab, Wi-Fi off): every check passed, including Raw series/Harmonized, the live card, a typed box and circle, downloads, all six pages, dark mode, and opening from WhatsApp | — |

## Things you should know

- **Cloudflare secret:** the first attempt saved the key as the secret's *name*. It was deleted and set again correctly (`FIRMS_MAP_KEY`, value encrypted). Because the key was briefly visible as a name, **request a new FIRMS key after the hackathon** and set it again with `npx wrangler@3 pages secret put FIRMS_MAP_KEY --project-name blindspot-firms` (paste the key only at the "Enter a secret value" prompt).
- **Building in Git Bash on Windows:** prefix the build with `MSYS_NO_PATHCONV=1`, or the live card breaks (written in `docs/DEPLOY.md`). PowerShell is fine.
- **Generating the project page:** edit `docs/templates/SUBMISSION.tmpl.md`, never `docs/SUBMISSION.md`. `make story` needs `data/processed/harmonized/calibration_factors.parquet`, which is only on your PC; on the second PC the page was rendered with the same code and the last real custom-area result (W-14).
- **Known small display detail, not changed:** for very small ratios the month card's two lines can differ in the second digit (Sangrur: 0.0075× and 0.0070×).

## What is left before 23:59 PKT

| Task | Who | Notes |
|---|---|---|
| **Video: choose, upload, test** | Aiza | Two options: her own recording, or the AI-assembled cut `docs/video/blindspot_demo_ai.mp4` (checked: 29.97 s, 1920×1080, silent, subtitles burned in). **If the AI cut is submitted, change the SI answer first**: it now says "We used no AI-generated images, video or voice" (edit `docs/templates/SUBMISSION.tmpl.md`, re-render, re-run `scripts/form_fields.py`). Upload publicly; test the link logged out |
| **Fill the form and press "Submit for Judging"** | Aiza | Field by field from `docs/SUBMISSION.md` (map in `YOUR_TASKS/10_submit_form.md`); tick both boxes; a banner confirms; you can resubmit until 23:59 |
| Make `Aiza166/nasa-hackathon` private | Aiza | Before the final submission (W-15) |
| Optional: FortiGuard classification for the new URL | Either | https://www.fortiguard.com/faq/wfratingsubmit, Company Name "N/A" |
| After the hackathon: new FIRMS key | Aiza | See above |

## Aiza's work on 15 Nov (after this note was first written)

| Commit | What |
|---|---|
| 4ed0316, 626adf2, 67911f1 | `scripts/form_fields.py` and `docs/FORM_PASTE.md`: one plain-text block per form field, with word counts (summary 189, description 540) |
| 37af739, fcfe81d | AI-assembled 30 s demo cut from real captures of the live app (`docs/video/ai_cut/`, `docs/video/blindspot_demo_ai.mp4`) |

## Commits from this session (all pushed)

```
19dc0b0 Deployed to https://blindspot-firms.pages.dev with the live current month (W10, W3)
17a965c Caution banner names the years per reason; legend covers months not yet in the archive
c29eead Video script: names and team name first, future line last (W-16)
6635893 Pages project name blindspot-firms (blindspot.pages.dev is taken)
9a983f0 Record team, Karachi Local Event and the 23:59 PKT deadline (W-15)
3ad6c70 W5/W6: rewrite the project page, person first, about 680 words
66e0708 Browser suite passes with the 2026 record; page shows 2003-2026
82022a1 W2: add January to October 2026 to the app data, provisional from August
819ad5c extend: keep the stored 2003-2025 baseline, move only the this-year line
9a883b4 Shorten the pre-event disclosure, list hackathon work, fix stale lines (W-13)
```
