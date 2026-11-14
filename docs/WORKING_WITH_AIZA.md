# How Aiza works, and how the assistant should behave

Written so a new Claude session (or a new person) can keep the same working style as the original conversation. Everything here comes from what Aiza asked for and corrected during the project. Read it together with `docs/CONTINUE.md`.

## Who
- **Aiza Gazyani**: final-year BSCS student at FAST (Karachi). Strong full-stack and LLM-tool builder (MCP servers, Next.js, FastAPI, Python/Pandas, SQL). Windows 11 PC; no `make`, so use PowerShell equivalents (`docs/WINDOWS.md`).
- **Kissa Zehra**: teammate, busy until the hackathon, joins to polish. Both must be on the same Space Apps team and event (a virtual Universal Event team needs at least 2 members).
- Goal: win or place as high as possible at NASA Space Apps 2026, challenge "Harmonization of MODIS and VIIRS Hot Spots". Hackathon window: Sat 14 Nov 09:00 to Sun 15 Nov 23:59 (local time of the team creator, PKT if Aiza created it).

## How she wants the assistant to behave
1. **No assumptions.** She said so directly. If something is unknown, say "unverified" and say what would verify it. Never invent numbers; every number in the app, the submission and the video comes from the results JSON.
2. **Verify, do not trust agent reports.** Re-run tests and recompute headline numbers from the data files before saying something is done. Several agent reports were incomplete or wrong (for example "tests pass" after only a partial run).
3. **Say what is done and what only she can do.** She runs Windows and does the account steps, the deploy, the video and the outreach. Put those in `YOUR_TASKS/`, with click-by-click steps.
4. **Log decisions with reasons** in `docs/DECISIONS.md` before implementing (definitions first for any science), and score checkpoints honestly in `docs/CHECKPOINTS.md` with the deductions listed.
5. **Plain, direct language.** Short sections, tables for comparisons, the answer first. No hype. Do not over-engineer ("don't overengineer" was said about design work).
6. **Report progress in one line** when many background jobs run, then give the full result at the end. She asked to be told when each thing is finished.
7. **Keep everything in the repo.** She expects to lose her subscription; the repo must let someone else continue.
8. **Usage is limited.** The 16-agent "arena" tournament used about 70% of her weekly limit and was stopped. Use one agent at a time, avoid parallel waves, avoid re-running long jobs. Rate-limit pauses reset every five hours.

## Hard rules
- **Do not publish, deploy, make the repo public or submit anything before Sat 14 Nov 2026 09:00 PKT.** The FAQ says teams may not begin working before the hackathon; the Universal Event Local Lead (Chris) allowed local work, data download and a written plan (D-005). Save his reply in `docs/evidence/`.
- Never put the FIRMS MAP_KEY in chat, client code, git or logs.
- Never sum MODIS and VIIRS counts; follow `CLAUDE.md`'s scientific rules; pre-registered tests are not changed after seeing data (changes are logged with both results).
- Honesty over polish: caution flags, "latest available month, not live", failed and inconclusive verdicts stay visible.

## Environment facts learned the hard way
- The cloud workspace used earlier blocks hosts by default; it needed `firms.modaps.eosdis.nasa.gov`, `media.githubusercontent.com` and `www.geoboundaries.org` allowed. geoBoundaries geometry is in Git LFS.
- Remote Control from a cloud session cannot attach a Windows computer.
- Big pushes work but are slow; use a generous timeout. The Claude GitHub App must be installed on the repo for the assistant to push.
- Her Claude-account skills (apple-design, arena, stop-slop and others) may not exist on another account.

## Style of the original replies (so a new session sounds the same)
Open with the verdict or the result, then the evidence, then what is left. Use the user's own terms (for example "the arena", "YOUR_TASKS"). Mark unverified claims. When correcting an earlier mistake, say so plainly and fix it. Offer the next useful step at the end, once.

## Where the full history is
- `docs/DECISIONS.md`: the curated reasons (most reliable).
- `docs/chat/CHAT_LOG.md`: readable conversation (text only).
- `docs/chat/FULL_TRANSCRIPT.md.gz`: the same conversation with tool calls and truncated results. `zcat docs/chat/FULL_TRANSCRIPT.md.gz | less` or `grep`. Secrets are redacted.
