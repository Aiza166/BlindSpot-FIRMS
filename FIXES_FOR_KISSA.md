# Fixes for Kissa's session, 15 Nov 2026

For Kissa and her Claude Code session. Written by Claude Code on Aiza's PC after a code review of everything that changed since the import commit (`git diff 850ae04..HEAD`: `pipeline/blindspot/extend.py`, the web changes for 2026, the story strip and the month card). Aiza's PC cannot deploy, so anything that must reach the public site has to be done on Kissa's PC.

**Deadline: tonight, Sun 15 Nov, 23:59 PKT.** The site is live and the tests passed on 14 Nov. Do not start a change you cannot finish, test and deploy with an hour to spare. Items 1 and 2 are worth doing tonight. Items 3 to 9 are safe to leave until after judging; write them down in `decisions.md` as known limits instead.

## How to use this file (prompt for Claude Code)

> Read `FIXES_FOR_KISSA.md`. Start with item 1: find out why `/api/nrt` returns 504 on the public site and tell me the cause before changing anything. Then do item 2. For each fix: write or update the test first, run `make test` and `make web-test`, log it in `ai-log.md` and `decisions.md`, make one small commit, and only then deploy with the steps in `docs/DEPLOY.md`. Do not touch items 3 to 9 unless I ask.

## What was checked and what was not

- Read in full: `pipeline/blindspot/extend.py`, the functions it calls in `calibrate.py` and `appdata.py`, and the diff of `web/components/*`, `web/lib/*`.
- Checked on the public site on 15 Nov at about 19:30 PKT: the pages load; `/api/nrt` fails (item 1).
- Not read: `tests/test_extend.py`, `web/e2e/run.mjs`, `web/lib/csv.ts` beyond a search, the NRT function body. No test was run on Aiza's PC.
- Items marked "not confirmed" are reasoned from the code and still need a failing test or a look at the data.

## Do tonight

### 1. The live current-month card fails on the public site (confirmed)

Three requests in a row, about 19:30 PKT:

```
curl "https://blindspot-firms.pages.dev/api/nrt?bbox=75.2,29.7,76.3,30.7&area=76128533B82601690264832"
{"status":"unavailable","code":"timeout","reason":"FIRMS did not answer in time"}   HTTP 504 after 10.1 s
```

The FIRMS website itself answered in 2 s at the same time. The card then shows the saved October month, so nothing looks broken, but the project page and the video script both say the current month comes in live.

What to find out, in this order:
1. `npx wrangler@3 pages deployment tail --project-name blindspot-firms` while loading the site: which FIRMS request times out.
2. Run the same FIRMS area URL by hand with the key on Kissa's PC (never paste the key into chat or a file): is FIRMS slow for this box, is the key over its transaction limit (the 2026 download used many requests), or is the key rejected?
3. `functions/_lib/nrt-core.ts`: `FIRMS_TIMEOUT_MS = 10_000` and the month is fetched in 5-day pieces (`MAX_DAY_RANGE = 5`). Mid-month that is 3 or more requests, each with a 10 s limit.

Likely fixes, smallest first: wait and retry if the key was rate limited; raise the per-call timeout; fetch the 5-day pieces in parallel instead of one after another. If it cannot be fixed tonight, change the wording instead: in `docs/templates/SUBMISSION.tmpl.md` say the live month is shown "when NASA's near-real-time service answers", and do not show the live card in the video.

### 2. Month card text is wrong while loading and after launch (confirmed by reading; small)

`web/components/MonthCard.tsx`, the last two paragraphs of the card:

- While the live request is still running (`nrt` is `null`), the card says "The live near-real-time service is not part of this build". On the public site every visitor reads that for the first seconds. Show a neutral "Loading the live current month…" for the `null` state.
- When the request fails, the card adds "The live current month appears here when the near-real-time service is switched on at launch." The site has launched. Remove that sentence, or show it only when `NEXT_PUBLIC_NRT_ENDPOINT` is unset.

Update the browser checks in `web/e2e/run.mjs` that read `card-live-note`.

## Leave until after judging (log as known limits)

### 3. `extend.py` cannot be run twice and is not atomic

`run()` rewrites all 350 area files in place and writes `index.json` last. If it stops midway, the next run fails with "new months must be contiguous". Adding November later fails with "extend appends one calendar year at a time, from January". The only way back is `git checkout -- web/public/data`. Fix: build the new files in a temporary folder and move them at the end, and let a run start from the month after `index.period.last`.

### 4. One night may be missing from January 2026 (not confirmed)

Rows are kept by local solar year, but FIRMS is downloaded by UTC date. In this box local time is UTC + 4 to 5.3 hours, so the night overpass of local 1 January is about 20:00 to 21:30 UTC on 31 December 2025. If the 2026 download started on 2026-01-01, those detections are not in the files. Check the first date in `data/raw/firms_2026/**/manifest.json`. If it is 2026-01-01, download 2025-12-31 too and re-run. The effect is one night in one month.

### 5. Standard and near-real-time rows for the same day (probably not triggered)

`filter_rows` drops duplicates on platform, time, latitude and longitude and keeps the first file. Per `decisions.md` W-12 the two products do not overlap in dates (VIIRS standard to 31 Jul, NRT from 1 Aug; MODIS standard to 31 Aug, NRT from 1 Sep), so this should not have happened. Add an assertion that no platform has both kinds of row on one local date, so a later run cannot double count.

### 6. `provisional_from` is taken after the filters and the mask

It should come from all downloaded rows. As written, a platform whose first NRT month has no surviving detection would get a later "provisional from" month. Not seen in the current data.

### 7. A slow `t1.json` can switch a visitor's own area to the raw view

`web/components/Explorer.tsx`, landing effect: the `.then` after `getJson("results/t1.json")` calls `setStory` and `setView("raw")` without checking that the area is still the story region. On a slow phone connection, someone who picks a district first gets the raw record with no explanation. Fix: inside the `.then`, do nothing unless the current area is still `land.id`.

### 8. The hotspot CSV does not mark provisional rows (rule 8; not fully confirmed)

The 2026 tiles hold near-real-time detections from August, with the same columns as before. `web/lib/csv.ts` has no mention of "provisional". CLAUDE.md rule 8 asks for the label in every CSV. Simplest fix: in `exportHotspots`, add a `provisional` column computed from `acq_date` and `constants.provisional_from[platform]`, and one header line that explains it.

### 9. Two small ones

- `extend.py` line 219 stores the "this year" ratio with 3 decimals; the month card shows the same ratio with more. This is the Sangrur 0.0070× next to 0.0075× noted in `HANDOFF_15NOV.md`. Store 4 decimals, or show both from the unrounded value.
- `appdata.validate_area_doc` does not check the length of the new `provisional` lists.

## Not code, but check before submitting

- If one of the AI-made videos is submitted (`docs/video/blindspot_demo_ai.mp4`, `blindspot_demo_brag.mp4`, or the voice-over cut), the "Use of Super Intelligence (SI)" text must change first: it currently says no AI video or voice was used. Edit `docs/templates/SUBMISSION.tmpl.md`, run `make story`, then `python scripts/form_fields.py`.
- The FIRMS map page says Suomi NPP data delivery ended on 1 Nov 2026. This agrees with W-12 (the series switches to NOAA-20 from November). No change needed; mention it if a judge asks.
