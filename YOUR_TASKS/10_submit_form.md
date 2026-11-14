# 10. Fill and submit the Space Apps form

**When:** Sat 14 Nov, early (the window closes Sun 15 Nov 23:59, local time of the team creator). **Time:** 1 h.

## What it is
The official project submission form on spaceappschallenge.org. The AI cannot fill it for you.

## Why it matters
Without a submission nothing else counts. Submit early, then fix if allowed.

## Field mapping
Field names below are from the 2026 Project Submission Guide (read 14 Nov, `docs/GUIDE_2026_NOTES.md`). The live form itself was not seen; check it matches.

| 2026 form field | Take it from `docs/SUBMISSION.md` |
|---|---|
| Project name | "Project name": Blind Spot |
| High-Level Project Summary | "High-level summary" and the bold one-sentence lead at the top |
| Link to Project Demo | "Link to Project Demo": YouTube URL from task 09 (≤30 s) or a ≤7-slide deck |
| Link to Final Project | "Link to Final Project": production URL from task 08; the repository URL is listed there too |
| Detailed Project Description | "Detailed description" (What it does, How it works, What we found and the limits, What is new, Other regions, Tools and languages, What was built when) |
| NASA Data | "NASA data used" table |
| Space Agency Partner Data and Other References | "Space agency partner data and other references" plus "References" |
| Use of Super Intelligence (SI) | "Use of Super Intelligence (SI)" section (names Claude Code by Anthropic). Judges do not see this field |

Before pasting, ask Claude to replace the placeholders in "Link to Project Demo" and "Link to Final Project" with the real links, in the **template** (`docs/templates/SUBMISSION.tmpl.md`), then `make story`.

## Steps
1. Sign in, open your team, find **Submit project** (name may differ).
2. Fill each field from the table. Add the team photo or screenshot if asked (`docs/screenshots/explorer-desktop-light.png`).
3. The form has **two confirmation boxes**: "Terms and Conditions" and "Confirm All Work is Original". Read each in full and tick only if true. Then click **Submit for Judging**; a banner confirms success.
   Before submitting: every field in English; no image, video or voice of anyone under 18; every link opens in a private window with no login; images pasted into the page are JPG/PNG/GIF up to 10 MB.
4. Save a draft, preview, check links in a private window.
5. Click Submit. Screenshot the confirmation. Check your email for a receipt.

## Record the result
`docs/CHECKPOINTS.md` H37 with date, time and URL. Tell Claude.

## Common problems
- **Character limits:** shorten the description; the summary and detailed text can be cut (ask Claude, keep numbers unchanged).
- **Video not accepted:** check allowed hosts and length in the 2026 guide.
- **Form closes at 23:59 Sun 15 Nov** in the Local Event's time zone; for the Universal Event, the Team Owner's local time (PKT if Aiza owns the team). You can resubmit until then; the last saved version is judged.
