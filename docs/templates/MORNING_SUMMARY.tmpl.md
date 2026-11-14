# Morning summary for the team lead

Template: `docs/templates/MORNING_SUMMARY.tmpl.md`, filled by `make story`. Numbers come from results JSON and the checkpoint table from docs/CHECKPOINTS.md.

## Done

| Block | What | Commits |
|---|---|---|
| 1 | FIRMS download, ingest, persistent-hotspot mask, QC | 932830b, f7eb46c, c8c14bc |
| 2 | Regions, calibration, splice, T1 | 70a14cb, 40f11f2, 680f5ea |
| 3 | T2/T2b, T1 re-evaluation, pitch from JSON | 72d3b45, 15ba752, 6afe439, a892982 |
| 4 | Static app data (`make appdata`) | 588c42b |
| 5 | Local web app (Next.js, MapLibre, DuckDB-WASM) | da7bc83 |
| 6 | Code, security and accessibility reviews, fixes | 5bf921d, cec8272 |
| 7 | Submission text, video script, subtitles, cold read, this summary (`make story`) | 22881ca |
| 8 | T3 explanation tests, reliability flags, use-case page, NRT function | b56b285, faa26bf, 23be852, 703e9fe |
| 9 | Submission and video rewrite after cold read; second cold read (docs/review/COLD_READ_2.md) | f90a5ff |
| 9b | Cold read 2 fixes: number sources moved to docs/SUBMISSION_SOURCES.md, inline screenshots, brief checklist, overclaims cut, one link line | 2479ce3 |
| 10 | Final check from raw, team names, deploy prep (headers, CSP, `make deploy-rehearsal`, docs/DEPLOY.md), outreach drafts (docs/OUTREACH.md), strict grade (docs/GRADE.md) | see `git log -1` |
| 11 | F1 (D-042): headline example in an unflagged year with the flagged 2025 case as contrast, one-sentence lead, critical periods (month level), median excluding flagged years, month-card fixes | see `git log -1` |

Pushed to the private GitHub repo (`origin main`). Nothing is deployed or public.

## Final check (1 Nov)

- `make ingest mask qc boundaries regions calibrate t1 t2 t3 appdata` from raw: 3,221 s (53.7 min), exit 0. T1/T2/T3, calibration and index JSON identical to the committed run except timestamps and the boundaries-manifest hash.
- `make test`: `192 passed, 1 skipped` (QA run, 2 Nov).
- `make web-test`: vitest `Tests 33 passed (33)`; Playwright `185/185 checks passed` (served with the production `_headers` and CSP); custom-AOI check `aqua_counts_match: true`.
- Deploy readiness: 4,022 files (limit 20,000), largest 21.1 MiB (limit 25 MiB); steps in `docs/DEPLOY.md`. Grade: `docs/GRADE.md` (19/25).

## Checkpoints

{{checkpoints}}

## Headline findings

- The 2012 sensor jump in Punjab is {{t1:results.hotspots.PK_Punjab.step_2012.raw_step|pct}} (Pakistan) and {{t1:results.hotspots.IN_Punjab.step_2012.raw_step|pct}} (India) raw; harmonized it is {{t1:results.hotspots.PK_Punjab.step_2012.harmonized_step|pct1}} and {{t1:results.hotspots.IN_Punjab.step_2012.harmonized_step|pct1}}. T1 step part passes in both.
- Pakistani Punjab T2: {{t2:t2.PK_Punjab.verdict_revised.label}}. T1: {{t2:t1_reevaluated.PK_Punjab.label}}.
- Indian Punjab T2: {{t2:t2.IN_Punjab.verdict_revised.label}} (evaluable years: {{t2:t2.IN_Punjab.verdict_revised.evaluable_test_years|len}}). T1: {{t2:t1_reevaluated.IN_Punjab.label}}. Held-out years inside the interval: {{t1:results.hotspots.IN_Punjab.heldout.n_inside|int}} of {{t1:results.hotspots.IN_Punjab.heldout.n|int}}.
- T3 (Indian Punjab): O {{t3:t3.IN_Punjab.evidence.O.verdict}}, T {{t3:t3.IN_Punjab.evidence.T.verdict}}, D {{t3:t3.IN_Punjab.evidence.D.verdict}}. Flagged years: {{t3:t3.IN_Punjab.reliability|caution}} (India), {{t3:t3.PK_Punjab.reliability|caution}} (Pakistan).
- Use case, headline (highest unflagged November since 2012): Sangrur {{usecase:sangrur.ym|year}} at {{usecase:sangrur.ratio|x2}} its November median (NOAA-20 {{usecase:sangrur.noaa20_ratio|x2}}; flag: {{usecase:sangrur.caution}}), Kasur {{usecase:kasur.ym|year}} at {{usecase:kasur.ratio|x2}} (NOAA-20 {{usecase:kasur.noaa20_ratio|x2}}; flag: {{usecase:kasur.caution}}). Contrast, {{usecase:month}}: Sangrur {{usecase:sangrur25.ratio|x2}} ({{usecase:sangrur25.caution}}), Kasur {{usecase:kasur25.ratio|x2}} ({{usecase:kasur25.caution}}).

## Open problems

- **VIIRS DOIs.** Now the LP DAAC V002 DOIs listed in `docs/REFERENCES.md`, checked on official catalog pages; no FIRMS-specific SP-archive DOI was found (D-039).
- **NRT is not live.** The month card shows the last archive month, labelled "not live". Live NRT needs the server function and the key on the host.
- **Pakistani Punjab T2 is inconclusive** ({{t2:t2.PK_Punjab.verdict_revised.evaluable_test_years|len}} evaluable test year).
- **Indian Punjab T1 fails** on held-out years; the cause is not settled (see above).
- **We changed the T2 verdict rule after seeing data** (D-034). The original verdict sits beside it in RESULTS_T2.
- **Deploy** waits for 14 Nov 09:00 (rules: nothing public before then). Headers, CSP and Pages config are ready and rehearsed (D-041). H26 stays open until the public URL works on a phone.
- **Teammate tasks:** P1–P5 are open (Local Lead email, second team member, MAP_KEY and Earthdata test, FIRMS docs read, 2026 guide read).
- **Pitch now gated on T3 (D-039).** The "moved later" clause appears only when T3 finds T supported for Indian Punjab (this run: {{t3:t3.IN_Punjab.evidence.T.verdict|raw}}), and it says "some" burning because D is {{t3:t3.IN_Punjab.evidence.D.verdict|raw}}.
- **Still open from the cold reads:** no independent check against non-FIRMS data (MCD64A1 rejected, D-008; official counts not obtained); T and D cannot be separated; blind re-score (COLD_READ_3) not yet run.
- **Video not recorded.** Script and subtitles are drafts (H34 🟡).
- **`make story` needs `web/e2e/artifacts/custom_aoi_check.json`**, which is gitignored; run `make web-test` first on a fresh clone.
- **User quote** for the project page is optional and not collected.
- **2026 submission guide:** field names, the 30 s limit and AI-statement rules come from the 2025 guide. Re-check on 13 Nov.

## What needs you

1. **Read the second cold read** (`docs/review/COLD_READ_2.md`), the T3 results (`docs/RESULTS_T3.md`) and `docs/GRADE.md` before recording the video.
2. **Read `docs/SUBMISSION.md` and `docs/VIDEO_SCRIPT.md`.** Edit the templates, never the outputs, then `make story`.
3. **Close P1–P5** with the team: send the Local Lead email, get a second member on the Universal Event team, test the MAP_KEY.
4. **13 Nov:** read the 2026 Project Submission Guide and update PLAN §0 and the templates.
5. **14 Nov, after 09:00 PKT:** deploy by `docs/DEPLOY.md` (Cloudflare account, `FIRMS_MAP_KEY` secret, smoke tests on a phone), then record the video from `docs/VIDEO_SCRIPT.md`.
6. **After the app is public:** send the drafts in `docs/OUTREACH.md`; quote only with written consent.
