# Blind Spot

A harmonized MODIS + VIIRS burning calendar for any area in Pakistan and northern India, which also tests whether the MODIS-to-VIIRS ratio stays constant over time. NASA Space Apps 2026, "Harmonization of MODIS and VIIRS Hot Spots". Full plan: `docs/PLAN.md`. Gates: `docs/CHECKPOINTS.md`.

## Repo layout

```
pipeline/   Python 3.11, DuckDB + Parquet. Ingest FIRMS, build cell-days, calibrate, validate, run T1-T4
web/        Next.js static export + MapLibre + DuckDB-WASM over Parquet tiles; one serverless function for NRT (key server-side)
data/raw/        downloaded FIRMS / MCD64A1 / boundaries (gitignored)
data/processed/  pipeline outputs: cell-day Parquet, calibration table, test results JSON
docs/       PLAN.md, CHECKPOINTS.md, critique, methods notes
.claude/    agents, commands, skills (adapted from ECC, see .claude/ECC-ATTRIBUTION.md)
```

## Commands

Keep this table current with the `Makefile`.

| Command | Does |
|---|---|
| `make install` | Create `.venv` (Python 3.11) and `pip install -e '.[dev]'` |
| `make data` | `download` → `ingest` → `mask` → `qc` → `boundaries` → `regions` → `calibrate` → `t1` → `t2` → `t3` → `appdata` (needs network access to FIRMS and GitHub LFS; run on your own computer). Override `COUNTRIES`, `YEARS`, `PRODUCTS`, e.g. `make data YEARS=2012-2025` |
| `make download` | Yearly country CSVs → `data/raw/firms/{product}/{year}/` + `manifest.json` (resumable, skips existing) |
| `make ingest` | Normalise raw CSVs → `data/processed/hotspots/year=…/platform=…/` Parquet with filter flag columns |
| `make mask` | Persistent-hotspot mask (year-round rule, D-024) → `data/processed/persistent_mask_cells.parquet`, `mask_report.json` |
| `make mask-compare` | Old (D-022) vs new (D-024) mask rule → `data/processed/mask_comparison.json` + `docs/MASK_COMPARISON.md` |
| `make qc` | `data/processed/qc_report.json` + `docs/QC_REPORT.md` |
| `make boundaries` | geoBoundaries gbOpen ADM1+ADM2 GeoJSON for PAK, IND → `data/raw/boundaries/` + `manifest.json` (licence, source, sha256; D-025) |
| `make regions` | Point-in-polygon of filtered detections → `data/processed/regions/point_regions.parquet`, `shapes.parquet`, `regions.json` (Punjab shapeIDs) |
| `make calibrate` | Masked daily/monthly counts (local solar date), Aqua→S-NPP and NOAA-20→S-NPP factors, splice → `data/processed/harmonized/*.parquet` (D-026, D-027, D-029) |
| `make t1` | T1 (D-028) → `data/processed/results/t1.json`, then `docs/RESULTS_T1.md` rendered from it |
| `make t2` | T2/T2b, mask report, T1 re-evaluation (D-033) → `data/processed/results/t2.json`, `data/processed/results/charts_t2.json` (web chart data), `docs/RESULTS_T2.md`, final T1 label in `docs/RESULTS_T1.md` (D-033, D-034) |
| `make t3` | T3 explanation tests O/T/D + reliability flags (D-039) → `data/processed/results/t3.json`, `docs/RESULTS_T3.md`, pitch sentence in `docs/PLAN.md` §2 (gated on T3) |
| `make appdata` | Static web data (D-035) → `web/public/data/`: `districts/*.json` (ADM2), `regions/*.json`, `index.json`, `districts.geojson`, `tiles/year=…/tile_{lat}_{lon}.parquet` + `manifest.json`, `constants.json`, `results/` (incl. `t3.json`), `ATTRIBUTION.md`; region/district JSON carry `reliability` (caution years + reason codes, D-039) |
| `make story` | Fill `docs/templates/*.tmpl.md` from results JSON → `docs/SUBMISSION.md`, `docs/VIDEO_SCRIPT.md`, `docs/video/subtitles.srt`, `docs/MORNING_SUMMARY.md`, each with a Number sources table (needs `make appdata` and `make web-test` outputs) |
| `make test` | `make lint`, then `pytest` (fixtures only, no network) |
| `make lint` | `ruff check` + `ruff format --check` (`make format` fixes) |
| `make web` | Install, build the static export (`web/out/`) and serve it on http://localhost:4173 (local only) |
| `make web-test` | ESLint, tsc, vitest (NRT function), build, serve, run Playwright e2e checks of every Must feature (screenshots → `docs/screenshots/`), then `web/e2e/check_custom_aoi.py`. Served with the production `_headers` + CSP |
| `make deploy-rehearsal` | Build (writes `out/_headers`, CSP meta, checks Cloudflare size limits), serve with headers, print them, run e2e. Deploy steps: `docs/DEPLOY.md` (D-041) |

NRT top-up (needs `FIRMS_MAP_KEY` in the environment): `.venv/bin/python -m blindspot.download --area-source VIIRS_NOAA20_NRT --area-start YYYY-MM-DD --area-end YYYY-MM-DD --out data/raw/firms_nrt`. FIRMS formats and what is verified: `docs/DATA_SCHEMA.md`.

## Scientific rules (never break these)

1. **Never sum MODIS and VIIRS** counts or FRP, and never add platforms together. Each platform is its own series; only the harmonized scale is compared across eras.
2. **Primary unit is calibrated hotspot counts on the VIIRS-S-NPP-equivalent scale** (splice rule in PLAN.md §4). Fire cell-days on 0.05°/0.1°/0.25° grids are a robustness check only.
3. Filters as in PLAN.md §4: standard data for history; `type == 0`; MODIS confidence ≥ 30; VIIRS confidence n/h; local solar time; persistent-hotspot mask on every series, NRT included.
4. **Calibrate Aqua MODIS → S-NPP VIIRS on 2012–2021 only**, per region × month. Bootstrap by year.
5. **Validate out of time on held-out 2022–2025.** Never a random split, never let 2022–2025 data touch calibration. Use prediction intervals, not CIs of the mean.
6. **Pre-registered tests (PLAN.md §4)** are fixed: regions PK Punjab and IN Punjab (geoBoundaries ADM1) reported separately, window 15 Oct–30 Nov. Do not change a threshold, window, region or metric after seeing data. If a change is truly needed, log it in `docs/PLAN.md` with the date and reason, and report both results.
   - T1: harmonized 2012 step < 10% of raw step; held-out part judged only if T2 finds no drift.
   - T2: overpass-controlled Aqua/S-NPP ratio; drift = 2022–25 mean outside the 2012–21 prediction interval, or Theil–Sen CI excludes 0. Report the Aqua-drift effect separately.
   - T2b: VIIRS night share and crossing-corrected Terra/Aqua ratio by year. Claim consistency, never proof.
   - Mask report: share of detections removed.
7. **Every number shown in the UI comes from pipeline output files** (Parquet/JSON via the API or precomputed JSON). Never type a number into code, copy or the pitch by hand. Pitch numbers are read from the results JSON.
8. **Label NRT data "provisional"** everywhere it appears (cards, charts, CSV column/header).
9. Scope statement in the app: "Coverage: Pakistan and northern India. The method should transfer to other regions."

## Coding rules

- Python 3.11. Lint and format with `ruff`. Tests with `pytest`. Type hints on public functions.
- Use parameterized DuckDB queries; never build SQL from user input with f-strings.
- TypeScript in `strict` mode; no `any` without a comment saying why.
- Accessible color ramps only (viridis/cividis); color is never the only signal.
- **FIRMS MAP_KEY lives only in the server environment** (`.env`, host secrets). Never in client code, never in a `NEXT_PUBLIC_*` variable, never in git, never in a session file or log. Copy `.env.example` to `.env` locally.
- Do not commit large data. `data/raw/` and big files in `data/processed/` are gitignored; small results JSON may be committed.
- Small, focused commits with clear messages.

## Workflow

1. **Plan**: `/plan` (or the `planner` agent) for anything touching more than one file. Check the plan against the scientific rules above.
2. **Small change**: one step of the plan at a time.
3. **Test**: write or update the test first for pipeline logic (`tdd-guide` agent, `python-testing` skill). Run `make test`.
4. **Verify**: run the `verification-loop` skill and fix what it finds.
5. **Review**: run the matching reviewer agent: `python-reviewer` (pipeline/), `typescript-reviewer` + `react-reviewer` (web/). Fix CRITICAL/HIGH findings.
6. **Log decisions**: any non-trivial choice (method, threshold, library, scope cut) gets an entry in `docs/DECISIONS.md` in the same commit: what, rejected alternatives, why, evidence.
7. **Commit**.
8. **Hand-off**: run `/save-session` at the end of a work block or before passing work to a teammate; the next person runs `/resume-session`. Session files go in `.claude/session-data/` and must not contain secrets.

Other agents: `architect` for design decisions, `build-error-resolver` for a broken `web/` build (it asks before cleaning caches or adding dependencies).

## Definition of done (per checkpoint)

A checkpoint is done only when its gate row in `docs/CHECKPOINTS.md` is ✅ with a working evidence link and a score. Nothing moves on until its gate passes. Record a ❌ with a reason rather than hiding it.

Gates are listed in `docs/CHECKPOINTS.md`: P0–P5 before the hackathon (no project code), H1–H37 during it.

For any code checkpoint, "done" also means: tests pass, `verification-loop` report is READY, a reviewer agent has no open CRITICAL/HIGH findings, and the scientific rules above still hold.
