# 07. Fri 13 Nov: read the 2026 submission guide and resources

**When:** Fri 13 Nov (checkpoint P5). **Time:** 1-2 h.

## What it is
The official 2026 Project Submission Guide and the challenge Resources tab are published on 13 Nov (`docs/PLAN.md` section 0). Our rules (30 s video limit, field names, AI-statement wording, theme) come from the **2025** guide and are marked as unconfirmed.

## Why it matters
A wrong format (for example a video over the limit, a missing field) can cost the whole submission. New official data or tools in the Resources could also help.

## Steps
1. Open https://www.spaceappschallenge.org/2026/ , sign in, find the **Project Submission Guide** and the challenge page **Resources** tab for "Harmonization of MODIS and VIIRS Hot Spots".
2. Read both. Write down, in a note: video length and format; whether slides are an option; each form field name; AI-use statement requirements; whether a code link or public repo is required; deadline and time zone; any new datasets or tools.
3. Paste the note to Claude with this instruction: "Compare with docs/PLAN.md section 0, docs/VIDEO_GUIDE.md section 1 and docs/SUBMISSION.md and tell me what to change."

## What Claude should update afterwards
- `docs/PLAN.md` section 0 (rules table, the warning markers).
- `docs/templates/SUBMISSION.tmpl.md`, `docs/templates/VIDEO_SCRIPT.tmpl.md`, `docs/templates/MORNING_SUMMARY.tmpl.md`: edit the templates, never the generated outputs.
- Then regenerate: `make story` (needs `make appdata` and `make web-test` outputs first; the file `web/e2e/artifacts/custom_aoi_check.json` is gitignored and made by `make web-test`).
- `docs/VIDEO_GUIDE.md` rules table; `docs/CHECKPOINTS.md` P5.

## Record the result
Save your note as `docs/GUIDE_2026_NOTES.md` (ask Claude to commit it) and tick P5.

## Common problems
- **Guide not published yet:** check the 2026 hub and Resources tab again later; do not guess.
- **Rules conflict with our plan:** tell Claude; the rule wins.
