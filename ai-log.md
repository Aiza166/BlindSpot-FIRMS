# AI log

A running record of where AI (the Space Apps rules call it Super Intelligence, SI) was used in Blind Spot, and what the people on the team decided. One row per piece of work. Add a row whenever AI writes code, text or data, or reviews something.

**Tool:** Claude Code (Anthropic). No AI-generated images, video or voice so far.

**Rule we follow:** AI is a tool. People choose the question, the scope and the tests, read every change, and approve it. Every number comes from pipeline output files, never from AI text.

## Before the hackathon (31 Oct – 2 Nov 2026)

Most of the code, tests, reviews and first drafts in this repository were written with Claude Code on 31 Oct to 2 Nov 2026, before the hackathon opened. The team lead reports that the Universal Event Local Lead allowed local work, data download and a written plan (`docs/DECISIONS.md`, D-005); the repository holds no written copy of that reply. The full record of that work is in `docs/DECISIONS.md` (D-001 to D-047) and `docs/chat/`.

That work was done in an earlier repository, `Aiza166/nasa-hackathon`. This repository, `Aiza166/BlindSpot-FIRMS`, starts on 14 Nov with one commit that imports it.

## During the hackathon (from 14 Nov 2026)

| Date | What AI did | What people decided or checked | Files |
|---|---|---|---|
| 14 Nov | Read the repository, the 2026 Project Submission Guide and the list of available tools | Aiza asked for the review and chose what to do next | none changed |
| 14 Nov | Aligned the documents with the 2026 guide: renamed submission sections to the 2026 form fields, added a tools section, added AI notes to the package metadata, updated the rules tables and task files | Aiza asked for the alignment. Not yet reviewed line by line by a team member | `docs/GUIDE_2026_NOTES.md`, `docs/SUBMISSION.md`, `docs/VIDEO_SCRIPT.md`, both templates, `docs/PLAN.md`, `docs/VIDEO_GUIDE.md`, `docs/CHECKPOINTS.md`, `docs/DECISIONS.md` (D-048), `YOUR_TASKS/08`, `YOUR_TASKS/10`, `README.md`, `pyproject.toml`, `web/package.json` |
| 14 Nov | Judged the project against the 2026 judging criteria and four 2025 winning pages; scored it about 18/25 | Aiza asked for a strict review and decided to act on it | none changed |
| 14 Nov | Wrote the weekend plan and started this log and `decisions.md` | Aiza set the direction: fix the gaps first, then deploy; two team members share the tasks | `docs/WEEKEND_PLAN.md`, `ai-log.md`, `decisions.md` |
| 14 Nov | Set up the new repository: copied the files, repointed repository links, wrote the "Project history" and "What was built when" disclosures, generalised the key-redaction rule in two scripts, wrote the import commit | Aiza chose the new repository and chose to disclose the earlier work | `README.md`, `HANDOFF.md`, `YOUR_TASKS/README.md`, `YOUR_TASKS/03_set_up_windows_pc.md`, `docs/SUBMISSION.md` and its template, `scripts/export_chat.py`, `scripts/export_chat_full.py`, `decisions.md`, `ai-log.md` |

## How to add a row

- **What AI did:** one plain sentence. Name the feature or document.
- **What people decided or checked:** who asked, who read it, what they changed or rejected.
- **Files:** the paths touched.

If AI ever produces an image, video or audio clip, note it here and add the visible watermark the rules require.
