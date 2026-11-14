# QA plan (v1, 1 Nov 2026)

Owner: QA pass before the 14 Nov deploy. Written before execution. Each check has a pass rule. Results go to `docs/QA_REPORT_FINAL.md` (not yet written) and `docs/CHECKPOINTS.md`.

## 0. Principles

1. **Every claim gets a check.** A check is pass, fail or not-run. "Not run" is written down with the reason, never hidden.
2. **Numbers come from pipeline files.** QA re-derives a sample of numbers from raw FIRMS data, independent of the code that produced the JSON (CLAUDE.md rule 7).
3. **Skeptic mode.** Each area asks "how would this be wrong and still look right?" before "does it run?".
4. **Nothing is published or deployed** before 14 Nov 09:00 PKT. QA runs locally and in the Playwright harness only.
5. **Low usage.** One review agent at a time; no arena; reuse existing review reports where the code has not changed.

## 1. Skills and practices used

Selected by name. Each must be read (SKILL.md) before it is run; the external repos were only skimmed (`agentic-awesome-skills` has 8,898 SKILL.md files; `claude-code-best-practice` is a guide, not a QA kit). External skills are reference only, never executed from the repo.

| Area | Skill / agent (source) | Use |
|---|---|---|
| Test strategy | `engineering:testing-strategy`, `agentic-council:craftsman-testing-strategy` | Map the risk areas to test layers; find gaps |
| E2E | `agentic-council:craftsman-e2e-testing`, `awt-e2e-testing` (external) | Playwright flow coverage, flake review |
| Edge cases | `agentic-council:skeptic-edge-case-enumeration`, `agentic-council:skeptic-failure-mode-analysis` | Enumerate inputs (empty, 1-day, 200k cap, dateline, border districts) |
| Data | `data:validate-data`, `analytics-skills:anomaly-detection-time-series` | Check the calibrated series for impossible jumps and gaps |
| Accessibility | `design-skills:accessibility-audit`, `accesslint-audit` (external) | WCAG 2.2 AA, keyboard, contrast, touch targets |
| Responsive | `vectorlab-ux-skills:viewports`, `keyboard`, `reduced-motion` | 375 to 1280 px, no overflow, focus order |
| UX | `design-skills:design-critique`, `website-design:web-review` | Hierarchy, copy, empty states |
| Performance | `agentic-council:tuner-performance-audit` | Payload size, cold load, DuckDB query time |
| Security | `security-review`, `backend-design:security-reviewer` | Key handling, NRT function, CSP, headers |
| Code | `code-review:code-review`, `superpowers:verification-before-completion` | Diff-level bugs; evidence before "done" |
| Adversarial | `adversarial-review:adversarial-review` (optional, only if budget allows) | Second opinion on the science claims |
| Cross-platform | `superpowers:systematic-debugging` when a Windows run fails | Root-cause, not guesses |

## 2. Risk areas (highest first)

1. **Scientific claims** (wrong number on the slide = biggest loss of credibility).
2. **Data integrity** (tiles, district JSON, CSV exports, critical flags, reliability flags).
3. **Headline flow on a phone** (the judge's first 30 seconds).
4. **NRT function and key handling** (security and quota).
5. **Accessibility and keyboard.**
6. **Cross-platform build (Windows).**
7. **Docs and submission text consistency.**

## 3. Checks and pass rules

### A. Scientific and data (area 1, 2)
- A1. Re-derive 10 random district-months (incl. 2 flagged, 2 Nov 2021) from `data/processed/hotspots` with an independent script. Pass: all within 0.1 of the JSON value. Current baseline: 8/8 (D-032); add 2 flagged cases.
- A2. Check `t1.json`, `t2.json`, `t3.json` against the numbers quoted in SUBMISSION, VIDEO_SCRIPT, subtitles and the use-case page. Pass: zero hand-typed numbers (grep for digits in templates against the JSON; `make story` output only).
- A3. Monotonic and sanity checks on `harmonized/*.parquet`: no negative counts, no NaN, no month with a factor outside [0.2, 5] without a note. Pass: or documented.
- A4. Filter checks: `type == 0`, MODIS confidence ≥ 30, VIIRS n/h; sum of removed fractions reconciles with `mask_report.json` (0.61%).
- A5. Dates: local solar date vs file-year boundary (open item H6, −2). Test a fire at 23:50 UTC on 31 Dec. Pass: assigned to the correct local year, or the gap is written in the report.
- A6. Coverage text: "Pakistan and northern India" and the reliability caution years match the JSON (CLAUDE.md rule 9).

### B. Data artefacts (area 2)
- B1. `web/public/data/manifest.json` sha256 matches every tile (run `make appdata` in a temp dir and diff; no network needed beyond FIRMS already cached).
- B2. CSV export: header row names match the documented columns; the 200k cap message appears exactly when the row count is above 200,000; the PNG export has the scale bar and attribution.
- B3. Regional JSON `critical` and `median_excl_flagged` equal the Python reference for 5 random districts and the 3 regions.
- B4. Reliability: a flagged year never appears as the headline example (D-042), checked for all district/region JSON.

### C. Web UI (area 3, 5, 6)
- C1. Existing gates still green: `make lint`, `make test`, `make web-test`, `npm run e2e:full` on Linux. Record counts.
- C2. Phone 360, 390, 414 px, and 1280 px desktop; light and dark; `prefers-reduced-motion` on. Pass: no horizontal scroll, primary answer above the fold on 390 × 844.
- C3. Keyboard only: tab order follows reading order on the month card and Explorer; all controls reachable; focus visible; Escape closes panels. Pass: no keyboard trap; screenshot of focus ring.
- C4. Touch drawing: CDP touch events draw a box and a radius with the pointer offset preserved; `touch-action` correct on the map (already tested by agent, verify).
- C5. Colour: the calendar uses cividis; colour is never the only signal (flag stripe + icon + text). axe 0 violations on all 6 pages × light/dark × 2 widths.
- C6. Empty and error states: no district selected, invalid bbox, network failure of the NRT card, DuckDB load failure. Pass: a message with a next action, no blank screen.
- C7. Performance: first contentful paint and total JS on a cold cache (Playwright, throttled 4G). Target: data loads on demand; the page is usable before the 116 MB tile set has finished. Record numbers in the report; no target number is invented beyond the stated budgets.

### D. NRT function and security (area 4)
- D1. Unit tests for `functions/api/nrt.ts`: origin check, rate limit, bbox snap 0.25°, current and previous month only, 10 s timeout, key never in the response body or headers (tested with a fake key `TEST_KEY_ONLY`).
- D2. Grep the built `web/out/` and the git history for `MAP_KEY` patterns and the hex third-party key fragment. Pass: zero hits.
- D3. `_headers` and the CSP meta match; `npm audit --omit=dev` 0 high.
- D4. Live key test is NOT run before 14 Nov; listed as a deploy-day check (`docs/DEPLOY.md`).

### E. Cross-platform (area 6)
- E1. Windows path: `docs/WINDOWS.md` commands are run on a Windows machine by the human (YOUR_TASKS/03). Until then the status is "not run on Windows", stated in the README.
- E2. `npm run e2e:full` works without the POSIX-only `HEADERS=1` (done by the running agent; verify on Linux).
- E3. `.gitattributes` keeps `*.parquet`, `*.csv` binary/LFS-correct; line endings in `.ps1` snippets are CRLF-safe.
- E4. Node version pinned (`.nvmrc`), `engines` set; `npm ci` from a clean clone in under 60 s on the container.

### F. Documentation and submission (area 7)
- F1. README, HANDOFF, YOUR_TASKS and CHECKPOINTS agree on the test counts (one source: the latest run).
- F2. Every number in SUBMISSION.md and VIDEO_SCRIPT.md has a row in the Number sources table.
- F3. Video script ≤ 30 s spoken (count words; target ≤ 75 words at 150 wpm); subtitles match the script.
- F4. No claim stronger than the tests support: "only because the sensor changed" must not reappear (grep).
- F5. AI statement present in SUBMISSION.md.

## 4. Test matrix

| Dimension | Values |
|---|---|
| Viewport | 360, 390, 414, 768, 1024, 1280 px |
| Theme | light, dark, forced-colors (spot check) |
| Motion | default, reduced |
| Input | mouse, keyboard only, touch (CDP) |
| Browser | Chromium (Playwright); Firefox and WebKit spot check if the browser is installed (not guaranteed) |
| OS | Linux (container, run now); Windows 11 (human, YOUR_TASKS/03); phone (human, 14 Nov) |
| Region | Sangrur, Kasur (headline); Lahore; an Indian district; a drawn area across the border; a 1-day range; a 200k+ row range |

## 5. Sequencing (avoid conflicts with the running agent)

1. Now (while the 4-items agent runs): write this plan; no edits to `web/`, `docs/screenshots/`, `docs/review/UI_*`.
2. When the agent reports: verify its claims myself (C1, C4, E2) before anything else.
3. Run A1–A6 and B1–B4 (pipeline and data; no web edits needed).
4. Run C2–C7 and D1–D3 in the Playwright harness.
5. Fix findings in order of risk area; each fix gets a test, a DECISIONS entry if it changes behaviour, and its own commit.
6. Write `docs/QA_REPORT_FINAL.md` with every check, its result, the evidence file, and what is still not run.

## 6. Reporting

- Each check: ID, result (pass / fail / not run), evidence path, reason if not run.
- Scores in `docs/CHECKPOINTS.md` change only when evidence exists. No self-scoring above what the evidence supports.
- Known open items carried forward (not hidden): H6 year boundary (A5), NOAA-20 era for custom AOI (review #2), no real-device phone test (C2, human), live NRT key test (D4, 14 Nov).

## 7. Out of scope for QA

- Scientific re-analysis beyond re-derivation (the T1–T3 design is pre-registered and fixed).
- Judge-facing presentation quality (handled in the video and submission reviews).
- Any deploy, public repo or submission before 14 Nov 09:00 PKT.
