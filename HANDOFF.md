# Handoff: read this first

**Start with `README.md` (overview), then `YOUR_TASKS/README.md` (what only the human can do, in date order) and `docs/CONTINUE.md` (how to continue with a new account or person, the first prompt to paste, repo transfer).** The chat is exported in `docs/chat/` (background only; `docs/DECISIONS.md` is the reliable record).

For a new Claude Code session, or a teammate, picking up **Blind Spot** (NASA Space Apps 2026, "Harmonization of MODIS and VIIRS Hot Spots"). Snapshot updated 1 Nov 2026 (originally 31 Oct).

## Prompt to paste into the new Claude Code session

> Read README.md, HANDOFF.md, CLAUDE.md, YOUR_TASKS/README.md, docs/DECISIONS.md and docs/CHECKPOINTS.md in that order. Follow CLAUDE.md's scientific rules strictly. Do not publish, deploy or submit anything before 14 Nov 2026 09:00 PKT. Never invent numbers: every number comes from pipeline output files. Log every non-trivial choice in docs/DECISIONS.md. Tell me the current state and the next YOUR_TASKS item.

## What this project is

A harmonized MODIS + VIIRS burning calendar for any district or drawn area in Pakistan and northern India, back to 2003. It also tests whether the satellite record itself shifted (orbit drift, fires moving to unobserved hours).
- Plan: `docs/PLAN.md`
- Decision history with reasons: `docs/DECISIONS.md`
- Progress gates: `docs/CHECKPOINTS.md`

## Rules that matter

- The hackathon runs Sat 14 Nov 09:00 to Sun 15 Nov 23:59 (local time of the team creator). The Participant FAQ says teams may not begin work before it. The Universal Event Local Lead told the team lead that local work, data download and a written plan are fine for now (D-005).
- **Do not publish or deploy anything before 14 Nov 09:00.** A private GitHub repo is fine.
- A Universal Event team needs ≥2 members on the same team.

## State (1 Nov 2026)

Built and tested locally; **not public**. See `docs/CHECKPOINTS.md` for gates and `docs/GRADE.md` (19/25).

| Item | Status | Where |
|---|---|---|
| Plan v2, decisions D-001 to D-042 | done | `docs/PLAN.md`, `docs/DECISIONS.md` |
| Pipeline: download to appdata; calibration, splice, T1, T2, T3 | done, rerun from raw 1 Nov | `pipeline/blindspot/`, `docs/RESULTS_T1.md` to `RESULTS_T3.md` |
| Web app (Next.js static export, MapLibre, DuckDB-WASM, NRT function) | done locally | `web/`, `docs/screenshots/` |
| Tests | `make test` 192 passed (1 skipped); vitest 33; Playwright 185/185; axe 0 violations (QA run, 2 Nov) | `tests/`, `web/e2e/` |
| Code, security, accessibility reviews | done | `docs/review/` |
| Submission text, video script, subtitles, outreach drafts, deploy steps | drafts ready | `docs/SUBMISSION.md`, `docs/VIDEO_SCRIPT.md`, `docs/OUTREACH.md`, `docs/DEPLOY.md` |
| Repo pushed to private GitHub | yes (`origin main`) | |

Key results: 2012 step +613% (PK) and +371% (IN) raw, +12.7% and -6.1% harmonized; Indian Punjab fails held-out years after 2021; Pakistani Punjab T2 inconclusive.

## Rebuild the data (only to re-run the science; the website data is already in the repo)

The `data/` folder is not included. It's regenerated from NASA FIRMS (no key needed for this part).

- **Mac/Linux:** `make install && make data && make test`
- **Windows:** follow `YOUR_TASKS/03_set_up_windows_pc.md` and `docs/WINDOWS.md` (PowerShell equivalents; untested on Windows; WINDOWS.md covers only the first four steps).

Expected: `make test` ends with about 192 passed (1 skipped). `docs/QC_REPORT.md` should show 90 downloaded files and 48 "unavailable"; those 48 are years before each satellite existed.

For the "current month" card later, request a free FIRMS MAP_KEY at https://firms.modaps.eosdis.nasa.gov/api/map_key and put it in `.env` (copy from `.env.example`). Never commit it or paste it into chat.

## Next steps (in order)

The human tasks are in `YOUR_TASKS/` (01 to 11). Summary:
1. Now: confirm the team event (Universal vs Karachi) and that Kissa is on the same team; FIRMS MAP_KEY; set up the Windows PC; Cloudflare account; OBS practice; outreach notes.
2. Fri 13 Nov: read the official 2026 submission guide; update PLAN section 0 and the templates; `make story`.
3. Sat 14 Nov after 09:00 PKT: deploy per `docs/DEPLOY.md`, test the live NRT card, record the video, submit early.
4. Sun 15 Nov 23:59: deadline.

## Open items

- Local Lead email, second team member on the same team, MAP_KEY, 2026 guide: `docs/CHECKPOINTS.md` P1 to P5 are still open.
- Check 2 or 3 coordinates from `docs/MASK_COMPARISON.md` on satellite imagery (optional).
- Open problems and limits: `docs/MORNING_SUMMARY.md`, `docs/CONTINUE.md` section 6.

## Git

From 14 Nov 2026 the work continues in the public `Aiza166/BlindSpot-FIRMS` (`origin main`), which starts with an import of the earlier `Aiza166/nasa-hackathon` repository (see "Project history" in `README.md`). Secrets: none in git; `.env` is gitignored.
