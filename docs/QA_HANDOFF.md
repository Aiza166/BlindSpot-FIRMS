# Handoff: what is done, what is left (2 Nov 2026)

Read first: `HANDOFF.md`, `docs/QA_PLAN.md`, `docs/DECISIONS.md` (D-046 and its amendment).

## The four items (D-046)
| Item | State | Evidence |
|---|---|---|
| 1. Phone answer-first, "Change area" panel | Done (Linux) | `web/components/Explorer.tsx` (`aria-expanded`, `aria-controls`); phone screenshots in `docs/screenshots/explorer-phone-*` |
| 2. Touch drawing | Done (Linux, CDP touch) | `web/e2e/run.mjs` touch checks, passing in `npm run e2e:full` |
| 3. Results "At a glance" + Methods | Results done; Methods numbering/glossary **not re-checked** | `web/app/results/page.tsx`; axe 0 on results and methods |
| 4. Windows safety | Done for files; **not run on Windows** | `serve.mjs --headers`, `scripts/e2e-full.mjs`, `web/.nvmrc`, `.gitattributes`, `engines` |

Verification run on 2 Nov (Linux): `npm run build` OK (4,028 files); `npm run e2e:full` 184/184; vitest 33/33; `tsc --noEmit` and lint clean.

## QA: done on Linux (2 Nov), see docs/QA_REPORT_FINAL.md
The text below is the earlier status, kept for history. Open items now live in the report's Findings table (Q-3 to Q-8) and Not-done list.

## (earlier) QA plan: NOT done
The QA subagents (sections A, B, D on Opus; section F on Sonnet) stopped at the 5-hour limit before writing reports. No QA report exists yet. Run them again per `docs/QA_PLAN.md` sections A–F:
- Opus 5.5: A1–A6 (re-derive numbers independently), B1–B4 (artefacts), D1–D3 (NRT and key handling).
- Sonnet 5.5: F1–F5 (docs consistency), C1–C7 (UI gates; C1 already passes as above), E1–E4.
- Write results to `docs/QA_REPORT_FINAL.md`. Do not claim a check passed without evidence.

## Still open
- Windows run of `docs/WINDOWS.md` (human, `YOUR_TASKS/03`).
- Live NRT key test and deploy: 14 Nov after 09:00 PKT only (`docs/DEPLOY.md`).
- Known limits: year boundary at 31 Dec (`QA_PLAN` A5), no real-device phone test.

## Rules that still hold
No publishing, deployment, public repo or submission before Sat 14 Nov 2026 09:00 PKT. No MAP_KEY in git or chat. Log every non-trivial choice in `docs/DECISIONS.md`.
