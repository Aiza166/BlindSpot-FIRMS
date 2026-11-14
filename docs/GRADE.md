# Strict judge grade (1 Nov)

Graded as a strict NASA Space Apps judge against the five judging criteria, 1–5 each. Evidence: the local app (`make web-test`, Playwright, 127/127 checks, screenshots in `docs/screenshots/`, built with the production CSP and headers), `docs/SUBMISSION.md`, `docs/RESULTS_T1-3.md`, `docs/VIDEO_SCRIPT.md`. Not yet public, no video recorded; a judge on 14 Nov sees only what is deployed and submitted.

## Judging criteria

| Criterion | Score | Evidence | What holds it back |
|---|---|---|---|
| **Impact** | 3 | Every Punjab district (347) gets a 2003–2025 calendar that no longer breaks in 2012 (+613% → +12.7% PK, +371% → −6.1% IN); month card compares a month with its median; CSV/PNG export (`explorer-desktop-light.png`, `use-case-desktop-light.png`). | No user has seen it. No quote from Rescue 1122, PDMA or an agriculture officer; impact is argued, not shown. NRT not live yet. |
| **Creativity** | 4 | Goes beyond the brief: tests whether the MODIS/VIIRS ratio is stable over time (T2), explains failures (T3: overpass drift vs later burning vs decline), flags caution years in the calendar with triangle + stripes + text; custom areas computed in the browser with DuckDB-WASM. | The calendar itself is a standard heatmap. |
| **Validity** | 4 | Pre-registered tests, calibration 2012–2021 only, held-out 2022–2025, prediction intervals, bootstrap by year; numbers flow from JSON (`make story`, number-source tables); full re-run from raw on 1 Nov reproduced every result number exactly. Honest limits list; post-hoc T2 rule change disclosed with both verdicts. | Indian Punjab T1 fails on held-out years; PK T2 inconclusive (1 evaluable year); no independent check against non-FIRMS data. A strict judge reads "fails/inconclusive" as partial validity even though it is honest. |
| **Relevance** | 5 | Hits every item of the challenge brief: AOI (district/box/radius), date range, calendar 2000s–present, current month vs median, accessible ramp (cividis, axe 0 violations in 24 runs), CSV and image download (table in SUBMISSION "How it meets the brief"). | — |
| **Presentation** | 3 | App is clean and readable on desktop and 390 px phone, light/dark (`explorer-phone-dark.png`); submission text is cold-read three times. | Video not recorded; submission is long (≈2,400 words) and dense; on the phone the calendar cells are small and the map is a thumbnail; the default view opens on a quiet December card, not the 2012 story. |
| **Total** | **19/25** | | |

## Engineering grade

| Area | Grade | Evidence |
|---|---|---|
| Tests | A− | `make test`: 179 passed (pytest, fixtures, no network) + ruff; `make web-test`: ESLint, tsc strict, vitest 24 passed (NRT function), Playwright 127/127 checks, Python cross-check of browser AOI (Aqua counts match). No load test of the function. |
| Reproducibility | A | `make ingest … appdata` from raw in 53.7 min (3,221 s) on 1 Nov; T1/T2/T3, calibration and index JSON identical to the committed run apart from timestamps and the boundaries-manifest hash (re-download time). Inputs hashed in provenance. Raw download needs FIRMS access. |
| Security | A− | Key server-side only, redacted in errors; origin check, rate limit, area/month allow-lists; CSP with script hashes (no `unsafe-inline` for scripts), frame-ancestors none, nosniff, Referrer/Permissions-Policy, HSTS (D-041). `style-src 'unsafe-inline'` remains; rate limit is per isolate. |
| Accessibility | A− | axe-core 0 violations across pages × light/dark × desktop/phone; cividis; flags not by colour alone; keyboard focus on calendar. No screen-reader test with a real user; Urdu UI absent. |

## Top 10 remaining improvements (ranked by expected score gain ÷ effort)

| # | Improvement | Criterion | Gain | Effort | Humans? |
|---|---|---|---|---|---|
| 1 | Record the ≤30 s video from `docs/VIDEO_SCRIPT.md` with subtitles | Presentation | +1 | 2 h | **Yes** (voice, recording) |
| 2 | Deploy on 14 Nov per `docs/DEPLOY.md`, set `FIRMS_MAP_KEY`, test NRT live on a phone (closes H26, H37) | Impact, Presentation | +0.5–1 (a dead link scores 1) | 1 h | **Yes** (account, key) |
| 3 | Get one or two real user replies (Rescue 1122 / PDMA / agri officer) via `docs/OUTREACH.md`, quote with consent | Impact | +1 | 3 days elapsed, 1 h work | **Yes** |
| 4 | Open the app on the 2012 story: default to PK Punjab, raw view, then a one-click "harmonize" | Presentation | +0.5 | 2 h | No |
| 5 | Cut the submission summary to ≤150 words with one picture; move detail below | Presentation | +0.5 | 1 h | Partly (final read) |
| 6 | Independent check against official stubble-burning counts (e.g. PRSC/CAQM Punjab season totals) | Validity | +0.5 | 1 day | **Yes** (find and cite the official numbers) |
| 7 | Phone calendar: larger cells or a single-year view; bigger map | Presentation | +0.3 | 3 h | No |
| 8 | Add NOAA-20 to the harmonized series from 2019 as a robustness line where Aqua drifts | Validity | +0.3 | 1 day (needs pre-registered note) | No (logged as a plan change) |
| 9 | Urdu labels for the month card and caution notes | Impact | +0.3 | 4 h | **Yes** (Urdu review) |
| 10 | Close P1–P5 (Local Lead email, team registration, 2026 guide check) | Eligibility (gate, not a score) | avoids disqualification | 1 h | **Yes** |
