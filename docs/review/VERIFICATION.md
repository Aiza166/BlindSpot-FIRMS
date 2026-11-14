# Verification report (verification-loop skill)

Date: 2026-10-31. HEAD: da7bc83. Scope: whole repo (pipeline Python via .venv, web/ Next.js). No source files modified.

```
VERIFICATION REPORT
==================

Build:     PASS (cd web && npm run build: 6 static routes, first-load JS 103-116 kB)
Types:     PASS (0 errors; web: npx --no-install tsc --noEmit)
Lint:      PASS (ruff check .: "All checks passed!"); web has NO ESLint (no lint script/config) - not added
Tests:     PASS (pytest "152 passed in 8.50s"; make web-test "56/56 checks passed" + custom-AOI check; coverage % not measured, no global target per skill)
Security:  PASS (0 issues)
Diff:      88 files changed, 18283 insertions(+), 9 deletions(-) over HEAD~10..HEAD; working tree clean except untracked data/

Overall:   READY for PR
Target:    NOT APPLICABLE (local-only verification)
Next permitted step: none

Issues to Fix / Notes:
1. web/ has no ESLint; only tsc guards TS code (note only, no tooling added).
2. One make web-test run logged a non-fatal "EADDRINUSE 0.0.0.0:4173" from the static server (port held by a previous run); checks still passed 56/56. The e2e harness could check/free the port first.
3. Custom-AOI parity: max_rel_diff 4.7%, 1 of 83 months differs >0.1 (documented: simplified Punjab polygons in browser).
```

## Phase detail

- Security grep: "sk-" hits are only `mask-*` false positives (data-testid, --mask-dir args). No `api_key` in TS/JS. `MAP_KEY` appears only in a comment in web/lib/nrt.ts stating the key never lives in the client. No tracked .env files. No console.log in web/.
- Diff review (last 10 commits, 70a14cb..da7bc83): pipeline modules added (appdata, boundaries, calibrate, regions, t1, t2, report_t1/t2, pitch, provenance) each with tests (test_appdata, test_boundaries, test_calibrate, test_t1, test_t1_pipeline, test_t2) - calibration/harmonization/T1-T2 logic is covered. Web app (A4) added with e2e harness (web/e2e/run.mjs). Large committed artifacts: web/public/data/results/t1.json (5.7k lines), t2.json (3.7k lines), 20 PNG screenshots (~0.1-0.9 MB each) - intentional but adds repo weight. No unintended changes spotted.

## Resolution (31 Oct, after D-038 fixes)
`make test` passes: 158 passed, ruff clean. `tsc --noEmit` reports 0 errors. `npm run build` passes (6 static routes). `make web-test` passes 56/56 checks plus the custom-AOI check (unchanged: 1/83 months, max 4.7%). `npm audit --omit=dev` finds 0 vulnerabilities. Note 2 is fixed: serve.mjs path check and Range. The EADDRINUSE harness note is not addressed.
