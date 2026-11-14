# QA scripts (2 Nov 2026)
Run from the repo root (`.venv/bin/python -I docs/qa/a1_recount.py`) with `data/processed` present.
`c_browser.mjs` needs the built site (`cd web && npm run build`) and uses port 4181; it hard-codes the path `/home/user/blindspot/web`, so change the two paths at its top when running elsewhere.
Results: `docs/QA_REPORT_FINAL.md`.
