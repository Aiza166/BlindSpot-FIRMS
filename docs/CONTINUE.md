# How to continue this project after the original chat ends

Written 1 Nov 2026. The original builder was one long Claude Code conversation with Aiza Gazyani. Aiza's subscription may end soon; this file lets Aiza (new plan) or a different person/Claude account carry on from the repo alone.

## 1. Open the repo in Claude Code

- **On a computer (local):** install Claude Code (https://docs.claude.com, search "Claude Code quickstart"), clone the repo, `cd` into it, run `claude`. Needs the account to have access to the repo (section 3).
- **In the browser:** https://claude.ai/code , connect GitHub (https://claude.ai/connect-github), install the Claude GitHub App on the repo (section 4), pick `Aiza166/nasa-hackathon`.
(Exact menu names change; both routes are unverified from here.)

## 2. First prompt for a new account or person

> You are continuing the project "Blind Spot" (NASA Space Apps 2026). You have no memory of earlier chats. Read these in order: README.md, HANDOFF.md, CLAUDE.md, docs/WORKING_WITH_AIZA.md (how to behave and what is forbidden), YOUR_TASKS/README.md, docs/DECISIONS.md, docs/CHECKPOINTS.md. Follow CLAUDE.md's scientific rules. Hard rule: do not publish, deploy or submit anything before Sat 14 Nov 2026 09:00 PKT. Every number must come from pipeline output files, never invented. Log non-trivial choices in docs/DECISIONS.md. Then tell me the current state in 10 lines and which YOUR_TASKS item I should do next.

`docs/chat/CHAT_LOG.md` is the readable exported conversation and `docs/chat/FULL_TRANSCRIPT.md.gz` is the full one with tool calls (see `docs/chat/README.md`). To get the same context as the original session, skim CHAT_LOG.md first (about 40,000 words) and search the full transcript for details. `docs/DECISIONS.md` is the reliable summary.

## 3. Moving the repo to another GitHub account

- **Easiest: add a collaborator.** GitHub, repo, Settings, Collaborators, Add people. The new person clones with their own login. History and ownership stay with Aiza.
- **Transfer ownership:** repo, Settings, General, Danger Zone, **Transfer** to the new account (the new owner must accept). Update the remote afterwards: `git remote set-url origin <new url>`.
- **Fork or copy:** `git clone` then push to a new private repo under the new account (history is kept).
- **Do not share secrets.** The repo contains none. `.env` is gitignored: the new person must get their own FIRMS MAP_KEY (`YOUR_TASKS/02_firms_map_key.md`) and recreate `.env` from `.env.example`. Cloudflare and GitHub logins are not shared either.
- **The website's data is in git** (`web/public/data`, 116 MB; D-045), so the site builds from a clean clone with `npm install` and `npm run build`. The raw NASA data and processed intermediates are not in git; rebuild only if you re-run the science (`docs/WINDOWS.md`, or `make data`).
- Check `docs/chat/CHAT_LOG.md` before making the repo public: it holds the conversation text.

## 4. Install the Claude GitHub App on the repo

Go to https://github.com/apps/claude (or follow claude.ai/connect-github), click Install, choose the account that owns the repo, select the repository `nasa-hackathon` (only this one), approve. HANDOFF.md earlier listed this as an open item; the repo was pushed to `origin main` on 1 Nov (per `docs/CHECKPOINTS.md` H1), so whether the App is installed is not recorded here.

## 5. Project state (1 Nov 2026)

- Built and tested locally: pipeline (`make test`: 192 passed, 1 skipped), web app (`make web-test`: vitest 33, Playwright 185/185, axe 0 violations), per `docs/CHECKPOINTS.md`.
- Results: `docs/RESULTS_T1.md`, `RESULTS_T2.md`, `RESULTS_T3.md`; submission text `docs/SUBMISSION.md`; video script `docs/VIDEO_SCRIPT.md`; self-grade 19/25 (`docs/GRADE.md`).
- **Not done:** public deploy, live NRT test, video, Space Apps form, team confirmation (P1, P2), MAP_KEY (P3), reading the 2026 guide (P5), a real user quote.

## 6. Open problems (honest)

From `docs/MORNING_SUMMARY.md` and `docs/ARENA_CONCLUSION.md`: Indian Punjab T1 fails on held-out years; Pakistani Punjab T2 inconclusive; later burning vs less burning cannot be separated; no non-FIRMS validation; a T2 rule changed after seeing data (D-034, disclosed); NRT card not live; 2026 form fields and rules unconfirmed (2025 values used); the Windows setup path is untested; `docs/WINDOWS.md` is stale (mentions 88 tests, covers only the first four pipeline steps). The Karachi vs Universal Event question is unresolved.

## 7. Ordered next steps through 15 Nov

1. Now: tasks 01 to 06 in `YOUR_TASKS/` (event confirmation, key, Windows setup, Cloudflare account, OBS, outreach notes).
2. Fri 13 Nov: task 07, read the 2026 guide, have Claude update PLAN section 0 and the templates, run `make story`.
3. Sat 14 Nov after 09:00 PKT: task 08 deploy and smoke tests, task 09 video, task 10 submit. Submit early.
4. Sun 15 Nov: verify, answer problems; deadline 23:59 (team creator's local time).
5. Afterwards: task 11.

## 8. Usage-limit tips

- One agent at a time; avoid the arena (the 16-agent tournament used about 70% of a weekly limit and was stopped early, `docs/ARENA_CONCLUSION.md`).
- Do the human tasks yourself; ask Claude only for edits and checks.
- Prefer small prompts with file names. Make Claude read `docs/DECISIONS.md` sections, not the whole repo.
- Long pipeline runs (about 54 min) cost your time, not tokens; run them in your own terminal.
- A 5-hour limit once stopped an agent mid-task; its work stayed saved but uncommitted. Commit often.

## 9. Rules and permissions history

- Participant FAQ: "Teams are not allowed to begin working on the challenges prior to the hackathon." (`docs/PLAN.md` section 0, quoted 31 Oct.)
- The Universal Event Local Lead (Chris, info@spaceappschallenge.org) allowed data download, a written plan and local work. This was relayed by Aiza in chat; decision D-005 records it. Aiza was to keep the email in `docs/evidence/`, which does not exist in the repo, so the proof is held by Aiza outside git.
- The permission covers the Universal Event only. If the team is registered under the Karachi Local Event, ask that Local Lead too (task 01).
- Publishing, deploying and submitting wait for 14 Nov 09:00 PKT.

## 10. What is saved in this repo, and what is not

**Saved here (everything needed to understand, rebuild, test and deploy the site):**
- All code: pipeline (`pipeline/`), website (`web/`), tests, scripts, the Claude Code agents/commands/skills the project uses (`.claude/`).
- Every decision with its reasons (`docs/DECISIONS.md`, D-001 onward), the plan, the checkpoints and scores, all reviews and critiques, the grade, the arena conclusion.
- The results of every test (`data/processed/results/*.json`, the `docs/RESULTS_*.md` reports) and the submission and video drafts.
- **The website's data** (`web/public/data`, about 116 MB), so a fresh clone builds with `npm install` and `npm run build` only. This was tested on a clean clone on 1 Nov 2026.
- The task list for the human (`YOUR_TASKS/`) and the readable chat log (`docs/chat/`).

**NOT saved here, and what to do about it:**
| Missing | Why | What to do |
|---|---|---|
| Raw NASA data (1.2 GB) and processed intermediates (about 570 MB) | Too big for git; re-creatable | Only needed to re-run the science. `make data` (or `docs/WINDOWS.md`) rebuilds it, about an hour, no key needed. Not needed to deploy. |
| `.env` with the FIRMS MAP_KEY | Secret, never committed | Request a new key (YOUR_TASKS/02). Without it the site still works; only the live "this month" card needs it. |
| The AI's memory of the conversation | It lives only in the old chat | `docs/chat/CHAT_LOG.md` has the text; `docs/DECISIONS.md` is the reliable summary. A new session starts blank and must read the files listed in section 2. |
| Account-specific skills (for example apple-design, arena) | They belong to the original Claude account | A new account may not have them. The project's own agents and skills in `.claude/` do travel with the repo. |
| The Local Lead's written permission | It was an email, not a file | Save a screenshot of it in `docs/evidence/` (see the README there). Do this once; it is your proof of what was allowed. |
| Accounts and links | GitHub App, Cloudflare, the team page, LinkedIn replies | These stay with their owner; the new person needs access, or Aiza does them (YOUR_TASKS). |

**Insurance, do this now, it takes five minutes:** on your own computer run `git clone https://github.com/Aiza166/nasa-hackathon.git`, then zip the folder and keep a copy (for example in cloud storage). That copy contains everything above even if GitHub or your Claude access is lost.
