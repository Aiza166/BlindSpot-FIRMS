# Weekend plan: 14–15 Nov 2026

Written 14 Nov after a judge-style review. Deadline: **Sun 15 Nov 23:59** (Team Owner's local time). Target: everything submitted by **Sun 18:00**, leaving the evening for fixes.

Status of each item is proposed until the team says go. Decisions and reasons: `decisions.md`. AI use: `ai-log.md`.

## What was checked, and what was not

| Checked on 14 Nov | Result |
|---|---|
| Official challenge page | Asks for a calendar "from the early 2000s to the present", colour ramps "across months", the "current month against the historical median", AOI selection, date range, CSV download |
| App data period (`web/public/data/index.json`) | 2003-01 to 2025-12. The 2026 tiles hold 61 detections, all dated 1 Jan 2026. So 2026 is missing |
| Calendar code and screenshots | Year × month grid. No daily view. The docs say "month-by-day" |
| `https://blindspot.pages.dev` | Taken by another project |
| 2025 winners (4 project pages) | Summaries of about 150 words, human problem first, live link, short details |

| Not checked | Why it matters |
|---|---|
| Rival projects on this challenge (Kiln Watch, Stubble Fire Watch) | Not findable by search on 14 Nov; project pages become public after submission. Nothing in this plan assumes what they built |
| The app running on this Windows PC | Never built here. First task below |
| Whether a FIRMS MAP_KEY exists | Needed for 2026 data and the live card |
| The challenge Resources tab | Could not be read without a login |

## Strengths (keep, and show them)

1. Harmonization that is tested, not asserted: fixed tests, held-out years, failures reported.
2. Reliability flags: the app says where its own correction stops working. No winner page we read does this.
3. Every brief item has a working feature: AOI (district, box, radius), date range, calendar, month against median, critical periods, accessible ramp, CSV and PNG.
4. Engineering: 186 Python tests pass here, browser tests and accessibility checks exist.
5. One clear finding: the 2012 jump is a sensor change (+613% raw, +12.7% harmonized in Pakistani Punjab).

## Weak points (ranked by how much they cost)

1. Nothing is live, recorded or submitted.
2. The record stops in Dec 2025; the brief says "to the present". The first card a judge sees is a quiet December 2025.
3. The project page is about 2,700 words and opens with a statistic. Winners open with a person and a problem.
4. No user has seen it. Impact is argued, not shown.
5. One region for a global brief.
6. Wording errors: "month-by-day", and the "starts in May, peaks in May and ends in May (May)" card.
7. Indian Punjab fails after 2021 and Pakistani Punjab is inconclusive. Honest, but a judge may read it as "does not work".

## How each score can move

| Criterion | Now | Realistic | What moves it |
|---|---|---|---|
| Impact | 3 | 3–4 | 2026 data and a live November card (W2, W3); one real reply (W8). Without a user reply it most likely stays 3 |
| Creativity | 4 | 4 | Already the strongest idea. The video and page must say it in one sentence |
| Validity | 4 | 4 | Do not chase a 5. A new independent check in 36 hours risks a wrong number. Make the failure read as a finding: "the app tells you when not to trust it" |
| Relevance | 4 | 4–5 | "To the present" closed by W2 and W3; wording fixed (W4); a clear line on extending to other regions (W6) |
| Presentation | 3 | 4 | 150-word summary, a page of about 600 words (W5), default view on the 2012 story (W7), a video that shows the live card (W9) |

Realistic total: **19–21 of 25**. That improves the chance of Global Nominee. It does not make a winner likely: roughly 10 of 11,500 projects won in 2025.

## Work items

Owner key: **A** = Aiza, **K** = Kissa, **C** = Claude Code (A or K reviews and approves every change).

| # | Item | Owner | Est. | Done when |
|---|---|---|---|---|
| W0 | Eligibility: email the Local Lead, confirm team and event, both members listed | A | 30 min | Written reply saved; screenshot of the team page |
| W1 | Build and run the app on this PC | C, A | 1 h | `npm run build` passes; site opens locally |
| W2 | Add 2026 to date (Jan–Nov) from the FIRMS area API, labelled provisional | C, A (key) | 3–4 h | Calendar shows a 2026 row; every 2026 value marked provisional; tests pass |
| W3 | Live current-month card (November 2026) | C, A (key) | 1–2 h after deploy | Card shows November 2026 with "provisional" on the public URL |
| W4 | Wording fixes: "month-by-day" → what the app shows; fix the critical-period sentence | C | 1 h | No "month-by-day" in the repo or app; the May sentence reads correctly; test added |
| W5 | Rewrite the project page: 150-word summary, about 600 words in all, detail moved to the Results page | C drafts, K edits | 2 h | K has read it aloud and changed what sounds wrong; numbers still come from the results files |
| W6 | Other regions: one honest paragraph on how to extend; no new region this weekend | C, K | 30 min | Paragraph in the page and the app's About |
| W7 | Default view opens on the 2012 story (Pakistani Punjab, raw), with a one-click "Harmonize" | C | 2 h | First screen shows the jump; browser test updated |
| W8 | Outreach: send the drafts in `docs/OUTREACH.md` once the link is live | K | 1 h + waiting | Messages sent; any reply saved with consent |
| W9 | Video, 30 s or less, with subtitles; shows the live card | K records, A checks numbers | 2–3 h | `ffprobe` shows ≤ 30.0 s; public link opens logged out |
| W10 | Deploy to Cloudflare Pages under a free name | A, C | 1–2 h | Public URL passes the smoke tests on a phone |
| W11 | Fill the form and press Submit for Judging | A | 1 h | Confirmation banner screenshot |
| W12 | Team name in the video, slides and page | A, K | 5 min | Name given to Claude |

## Order and timing

**Saturday**
1. W0 and W12 now (A). W1 in parallel (C).
2. W4, then W7 (C). K starts W5 with Claude's first draft.
3. W2 as soon as the MAP_KEY is in `.env` (A gets the key; C runs it).
4. End of day: all tests green, K has approved the page text.

**Sunday**
1. Morning: W10 deploy, W3 live card, phone smoke test (A, C).
2. W8 outreach goes out as soon as the link is live (K).
3. W9 video (K), numbers checked (A).
4. W11 submit by 18:00. Evening: fix what breaks, resubmit if needed (the last saved version is judged).

## What we are not doing, and why

- **A second calibrated region.** A new region needs a fresh download and calibration and its own tests. The pipeline has never run on this PC. A rushed region with untested factors would cost Validity more than it adds to Relevance.
- **A daily calendar.** The brief asks for colour ramps "across months". The fault is our wording, not the feature.
- **A new independent validation.** Not enough time to do it carefully.

## Risks

| Risk | Plan |
|---|---|
| Pre-event work | W0. The page states plainly what was prepared before 14 Nov and what was built during the event. See `decisions.md` W-01 |
| No MAP_KEY in time | W2 and W3 drop out; the page says the record ends Dec 2025 |
| Build fails on Windows | Fix first (W1) before any feature work |
| 2026 data is near-real-time for recent months | Label provisional everywhere (rule 8); keep it out of calibration and medians unless the month is complete |
| Video runs long | Cut words, never speed up the voice; 7 slides as the fallback |
