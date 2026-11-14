# Decisions (hackathon weekend, from 14 Nov 2026)

Each entry: what was decided, why, what was rejected, and who decided. Earlier decisions (D-001 to D-048, 31 Oct to 14 Nov) are in `docs/DECISIONS.md`.

Status: **Proposed** = Claude's recommendation, waiting for the team. **Agreed** = a team member said yes.

## W-01 · Say plainly what was built before the hackathon
- **Status:** Agreed by Aiza, 14 Nov ("yes, disclose it").
- **Decision:** Wherever the code lives, the project page, README and `ai-log.md` state that the pipeline and app were prepared on 31 Oct to 2 Nov, and list what was built during the event.
- **Why:** The Participant FAQ says teams may not begin work before the hackathon. The submission form asks the team to confirm the rules were followed. A new repository changes where the code is stored, not when it was written. If the history is hidden and a judge or organiser finds out, the likely result is disqualification; if it is disclosed with the Local Lead's written permission, the team has an answer.
- **Rejected:** Presenting the existing code as work that started on 14 Nov. Claude will not write a log, commit history or page text that says so.
- **Done 14 Nov:** "Project history" in `README.md`, "What was built when" in `docs/SUBMISSION.md`, and the first section of `ai-log.md`.
- **Open:** the Local Lead's written reply.

## W-02 · New repository
- **Status:** Agreed by Aiza, 14 Nov. Repository: `Aiza166/BlindSpot-FIRMS`.
- **Decision:** The new repository is the public home for the weekend's work. Its first commit says it imports the code prepared earlier, and W-01 applies. The two chat-export scripts were changed in the import so they no longer contain the first 8 characters of a third-party key; the rule now redacts any 32-character hex string. Personal email addresses were removed from the two chat exports in `docs/chat/` (22 places).
- **Why:** It also drops the old history that contains the first 8 characters of a third-party key (`docs/QA_REPORT_FINAL.md`, Q-3).
- **Rejected:** A first commit that reads as a fresh start.

## W-03 · Fix the "month-by-day" wording; do not build a daily calendar
- **Status:** Proposed.
- **Decision:** Change the README, submission and app text to say what the calendar shows: one cell per month, one row per year.
- **Why:** The official brief asks for colour ramps "across months". The app already does that. The error is in our description.
- **Rejected:** Building a daily view this weekend (not asked for, and it costs hours needed elsewhere).

## W-04 · Add 2026 to date from the FIRMS area API, marked provisional
- **Status:** Proposed. Needs a FIRMS MAP_KEY.
- **Decision:** Fetch January to November 2026 for the coverage box and show it as a 2026 row, labelled provisional. Keep it out of calibration, and out of medians unless the month is complete.
- **Why:** The brief says "from the early 2000s to the present". The app's data ends in December 2025; the 2026 tiles hold only 61 detections dated 1 January.
- **Rejected:** Leaving the record at 2025 and relying on the live card alone (ten months of 2026 would still be missing).
- **Rules kept:** `CLAUDE.md` scientific rules 3, 5 and 8.

## W-05 · No second region this weekend
- **Status:** Proposed.
- **Decision:** Keep Punjab. Add one paragraph on how the method extends to other regions.
- **Why:** A new region needs its own download, calibration and tests, and the pipeline has never run on this PC. Untested factors would weaken the strongest part of the project.
- **Rejected:** A quick extra region to look global.

## W-06 · Rewrite the project page for a reader with no background
- **Status:** Proposed.
- **Decision:** A summary of about 150 words that opens with a person and a problem, and a page of about 600 words. Test details move to the app's Results page.
- **Why:** The four 2025 winning pages we read are short and open with a human problem. Ours is about 2,700 words and opens with a statistic.
- **Rejected:** Cutting the limits and the failed test from the page. They stay, in two or three plain sentences.

## W-07 · Open the app on the 2012 story
- **Status:** Proposed.
- **Decision:** The first screen shows Pakistani Punjab in the raw view with the 2012 jump, and one button to harmonize.
- **Why:** The first screen now shows a quiet December 2025 card. A judge gives a project a few minutes.
- **Rejected:** Keeping the current default and relying on the video to tell the story.

## W-08 · Do not chase a higher Validity score with a new check
- **Status:** Proposed.
- **Decision:** No new independent validation this weekend. Present the after-2021 failure as what it is: the app tells the user when not to trust the number.
- **Why:** A rushed comparison against outside figures risks a wrong number on the page.

## W-09 · Task split
- **Status:** Proposed.
- **Decision:** Aiza: eligibility email, team and event check, FIRMS key, Cloudflare deploy, number checks, the form. Kissa: page edit, outreach, video recording. Claude Code: code and first drafts, reviewed by a team member before each commit. Full table in `docs/WEEKEND_PLAN.md`.
- **Why:** Account, key, voice and submission steps can only be done by a person; the two members can work in parallel.
