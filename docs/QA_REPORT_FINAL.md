# QA report (2 Nov 2026, Linux container)

**Update after follow-ups (D-047):** Q-2, Q-4, Q-6, Q-7 and Q-8 are closed (details in the table). Browser suite is now 185/185 (one new check for the Methods factor paragraph).

Plan: `docs/QA_PLAN.md`. Run on the repo at commit 553125b plus the fixes listed under Q-1 and Q-2 below. The three QA subagents hit the usage limit and wrote no reports, so every check here was run directly. Scripts: `docs/qa/` (copied from the scratchpad). Nothing was deployed or published.

## Summary

| Area | Result |
|---|---|
| A science and data | Pass, with 3 low findings (Q-4, Q-6, Q-7). Re-derived raw counts, splice, ratios, mask, medians independently. Calibration factors were not refit. |
| B data artefacts | Pass |
| C web UI | Pass on Linux/Chromium. Not run: real phone, Firefox/WebKit, forced-colors |
| D security | Pass, with 1 low finding (Q-3) |
| E cross-platform | Partial. Linux pass; **not run on Windows** |
| F docs | 2 findings fixed (Q-1, Q-2); 1 open (Q-8) |

## Checks

| ID | Result | Evidence |
|---|---|---|
| A1 raw counts | PASS | `docs/qa/a1_recount.py`: own filters (standard, type 0, MODIS conf ≥ 30, VIIRS n/h, 0.01° mask, local solar month) on 7 districts incl. Lahore, Sangrur, Kasur: 7,728 platform-month cells, 0 mismatches |
| A1 splice | PASS | Sangrur, Kasur, Lahore: harmonized equals the S-NPP raw count in 108/108 months 2013–2021 |
| A1 headline | PASS | Sangrur Nov 2021 = 8,056 (S-NPP raw 8,056); 8,056/4,617 = 1.74×. Kasur 393/203 = 1.94×. NOAA-20 ratios 1.94× and 1.76× reproduce with a 2019–25 median |
| A2 numbers in text | PASS | `make story` regenerates SUBMISSION, VIDEO_SCRIPT and subtitles byte-identical; template scan finds 0 hand-typed figures with units (heuristic) |
| A3 sanity | PASS | 289,800 series values: 0 negative, 0 NaN. Factors 0.52–18.2, none null (see Q-7) |
| A4 mask | PASS | Removed counts equal `mask_report.json` exactly (667 / 10,112 / 15,539 / 914). In-box totals match, S-NPP off by 1 (Q-6) |
| A5 date boundary | PASS with finding | Local solar date = UTC + lon/15 h, max error 1.2 µs. 31 Dec/1 Jan handled. First local day of 2003 is short (Q-4) |
| A6 scope text | PASS | "Pakistan and northern India" present in 5 places |
| B1 tiles | PASS | 3,597 tiles, 0 row-count mismatches vs manifest; total 4,747,340 vs independent 4,747,341 (Q-6) |
| B2 CSV/PNG | PASS | Covered by `make web-test` (CSV cap message, both PNG exports, hotspot CSV) |
| B3 medians | PASS | 25 districts + 3 regions, 336 month values: max difference 0.05 (one-decimal rounding) |
| B4 flagged years | PASS (2 districts) | Sangrur and Kasur: 2021 is not in `reliability.caution_years` (Sangrur 2022–25, Kasur 2023–25). Not checked for all district files: the headline rule applies only to the two use-case districts |
| C1 gates | PASS | `make test` 192 passed, 1 skipped; `make web-test`: lint, tsc, vitest 33/33, 185/185 browser checks (184 at the time of the first run), custom-area check; `npm run e2e:full` 184/184 |
| C2 viewports | PASS | `docs/qa/c_browser.mjs`: 360, 390, 414, 768, 1024, 1280 px: no horizontal scroll; month card starts at 331 px on 360–414 wide phones (above the fold) |
| C3 keyboard | PASS | Tab order at 390 px: skip link, nav, theme, Change area, month card controls; 14 distinct stops, focus indicator present |
| C4 touch | PASS | Touch checks in e2e (picker, calendar cell). Real device not tested |
| C5 axe | PASS | 0 violations, 6 pages × light/dark × 2 widths |
| C6 error states | PASS | No-match search shows a message; impossible box (north 95, west > east) refused with "Enter west < east and south < north…"; with the DuckDB engine blocked the page still renders, 0 uncaught errors |
| C7 performance | INFO | Cold load at 390 px, ~1.6 Mbps, 150 ms, 4× CPU: month card 11.8 s, ~1.5 MiB by content-length. No product target exists; budget used 20 s |
| D1 NRT unit tests | PASS | vitest 33/33 (origin, rate limit, snap, month window, redaction) |
| D2 key leakage | PASS with finding | Built site: 0 `MAP_KEY`, 0 32-hex strings in js/html/_headers; no env file tracked except `.env.example`; test key is `0123456789abcdef`×2; `NEXT_PUBLIC_NRT_ENDPOINT` is a URL only. Q-3 below |
| D3 headers/audit | PASS | `npm audit --omit=dev` 0 vulnerabilities; CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy, X-Content-Type-Options in `_headers`; `frame-ancestors 'none'` |
| E1 Windows | NOT RUN | No Windows machine. `docs/WINDOWS.md` untested there |
| E2 e2e without POSIX | PASS | `npm run e2e:full` ran 184/184 |
| E3 gitattributes | PASS | Present (LF text; binary parquet/png/wasm/gz) |
| E4 clean install | PASS | `npm ci` from `git archive HEAD web`: 27 s |
| F1 test counts | FIXED | Q-1 |
| F2 number sources | PASS | See A2 |
| F3 video length | PASS | Voice-over 54 words, within the 30 s script; subtitles regenerated and match |
| F4 overclaims | FIXED / OPEN | "only because" absent. Q-2 fixed; Q-8 open |
| F5 AI statement | PASS | `docs/SUBMISSION.md` line 141 |

## Findings

| ID | Severity | Status | What and what was done |
|---|---|---|---|
| Q-1 | Low | Fixed | README, HANDOFF, CONTINUE and the MORNING_SUMMARY template still said 189 passed / vitest 28 / Playwright 146. Now 192 (1 skipped) / 33 / 184, summary regenerated. CHECKPOINTS and GRADE rows keep the counts from their own dates on purpose. |
| Q-2 | Medium | Fixed | Voice-over and the PLAN §2 pitch now state the October–November season. The pitch also quotes the harmonized steps from `t1.json` (+12.7% and -6.1%) instead of "removes it" (the step is reduced, not zero); word cap 45 → 55 (D-047), pitch is 52 words. |
| Q-3 | Low | Open | The first 8 hex characters of a third-party key are in `scripts/export_chat_full.py` and `scripts/export_chat.py` (redaction rule) and in git history (commits 22a3694, 553125b). The readable chat log no longer contains it. 8 of 32 characters is not usable, but decide before making the repo public: accept it, or rewrite history. |
| Q-4 | Low | Closed, not a defect | Tested instead of assumed: downloaded the 2002 MODIS files and mapped every 31 Dec 2002 detection to local solar date. None lands on 1 Jan 2003. Both platforms have data on 1 Jan 2003; the missing January 2003 days are Aqua 30 Jan and Terra 2, 17, 27, 29, 31 Jan. The 2002 files were deleted again so `make ingest` is unchanged. Residual: a day counts as available if it has any detection (D-026), so a real zero-detection day looks like an outage; rare at this scale, not measured. |
| Q-5 | Low | Open | District JSON provenance says `code_dirty: true`, so the data was built from uncommitted code. Rebuild `make appdata` from a clean tree before 14 Nov and check that only provenance changes. |
| Q-6 | Info | Closed | Cause found: `hotspots_filtered` drops exact duplicate rows; one S-NPP row is duplicated (2024-05-09 08:26 UTC, in `viirs-snpp_2024_India.csv`). The recount did not de-duplicate. The pipeline is right. |
| Q-7 | Info | Closed | The Methods page now explains the factors with the range (0.5 to 18.2), median (7.5) and "above 1 in 35 of 36 region-months", all read from `calibration.json`, citing Schroeder et al. 2014. The only factor below 1 is Indian Punjab in August. e2e checks the printed range. |
| Q-8 | Low | Fixed | Submission text now gives both ratios: Sangrur 1.74× the 2003–2025 median, or 1.62× against the median with flagged years left out; Kasur 1.94× or 1.84×. The video says "its November median" instead of "the usual November". README updated. |

## Not done or not covered

- **Calibration refit:** the Aqua→S-NPP factors and T1–T3 were not re-derived. They are pre-registered and out of QA scope. Raw counts, splice, ratios, mask, tiles and medians were.
- **Windows (E1)**, a real phone, Firefox and WebKit, forced-colors mode, and the live NRT key test (14 Nov only).
- **Throttled performance** covers the month card only; the tile download for custom areas was not timed.
- **Code review of the new D-046 changes** was not run as a separate reviewer pass.
