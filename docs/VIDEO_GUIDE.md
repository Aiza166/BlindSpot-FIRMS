# Blind Spot: video guide

Do this LAST (H30–H34), after the app works and results JSON is final. §1 was checked against the 2026 Project Submission Guide on 14 Nov (`docs/GUIDE_2026_NOTES.md`); ✅ = confirmed there, ❓ = unknown.

## 1. Hard rules

| Rule | Status |
|---|---|
| ≤30 s video (English, or English subtitles), OR ≤7 slides incl. title and intro, in English. Over the limit = not eligible for Global Judging | ✅ |
| Public link, opens with no login, password or permission | ✅ |
| Order: 0:00 your names and team name → 0:02 challenge and why → 0:05 title/tagline → 0:10 how it works, user experience, NASA and partner data → 0:20–0:30 future impact | ✅ (suggested by the guide) |
| SI (AI)-generated images/video carry a visible watermark; SI audio acknowledged in text and metadata | ✅ |
| SI statement names every AI tool, including brag/Hyperframes/Kokoro if used | ✅ (form field "Use of Super Intelligence (SI)") |
| No NASA branding (logos, flags, mission identifiers) in generated content | ✅ |
| No image, video or voice of anyone under 18 | ✅ |
| Slides show team name, member names, challenge, an image of the project, the user experience, and how NASA/space-agency data make it possible | ✅ |

Order rule vs D-011: names and challenge go on screen at 0:00; the outcome line is the first thing spoken.

## 2. Shot list (30 s)

Fill `{…}` ONLY from results JSON; note each key and value beside the script. If T2 finds no drift, use the no-drift script (PLAN §4) for line A.

| Time | Picture | On-screen text | Voice-over |
|---|---|---|---|
| 0:00–0:04 | Title card | `{Team names}` · `{Challenge name}` | A: "Read raw, Punjab's fire record is off by {X%}." |
| 0:04–0:08 | App home, PK Punjab selected | **Blind Spot**: fire calendar, 2003–today | B: "Blind Spot corrects it for any district, back to 2003." |
| 0:08–0:20 | **Calendar, raw → harmonized toggle** (the one visual), with sensor eras shaded | "NASA FIRMS: MODIS + VIIRS" · "2012 step: −{STEP%}" | C: "It puts NASA FIRMS MODIS and VIIRS fires on one scale. Raw, then harmonized: the 2012 sensor jump shrinks by {STEP%}." |
| 0:20–0:26 | Current-month card, then CSV download | "This month vs median: {RATIO}" · "provisional" | D: "Pick a district, see if this month is unusual, download the data." |
| 0:26–0:30 | End card | "For emergency managers in Pakistan and India" · `{URL}` | E: "Blind Spot. Free, at {URL}." |

VO: 57 words (limit 70). Say "we test", never "first".

## 3a. Path A: brag (optional)

**What it is:** an agent skill (MIT, v0.5.0, commit `669ab92`). The agent reads project source, writes a plan, builds an HTML/CSS composition; Hyperframes (HeyGen, `npx hyperframes`) renders `brag.mp4`. No screenshots needed; it recreates the UI rather than recording it.

**Needs:** Node 22+, FFmpeg, Hyperframes CLI, a paid coding-agent plan. No API keys. Kokoro voice (`--voice`) is local. letsbrag.app (hosted, price ❓) needs a public URL.

**Steps:**
1. `node -v; ffmpeg -version; npx hyperframes doctor`
2. Install in the project only: `npx skills add https://github.com/latent-spaces/brag --skill brag` (no `-g`). Read the installed files first (D-013 rule).
3. Write `video/brief.md`: shot list, exact copy, filled numbers, order rule, "no invented numbers".
4. In `web/`: `/brag --full --tone polished --duration 25 --no-sfx --title "Blind Spot"`, then "follow video/brief.md exactly". `--full` keeps Hyperframes; on Opus 5.5 it otherwise switches to brag-slim.
5. Check `brag-output/brag-plan.md` against results JSON; `npx hyperframes preview`.
6. Burn in the subtitles and watermark (needs libass and freetype):
   `ffmpeg -i brag.mp4 -vf "subtitles=video/blindspot.srt,drawtext=text='AI-generated video (brag/Hyperframes)':x=24:y=24:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.6" -c:a copy final.mp4`

**Licence:** code MIT; music CC BY 4.0, credit "Music: Sascha Ende, ende.app (CC BY 4.0)"; SFX CC0. Name brag, Hyperframes and the agent in the AI statement.

**Risks:** brag's gate caps at 25 s (compress the shot list); no subtitle feature; recreated UI may differ from the app or show made-up "real-looking" numbers; `npx` pulls unpinned npm code; output is AI-generated video, so the watermark stays on throughout.

## 3b. Path B: manual (default)

1. OBS Studio: 1920×1080, 30 fps, MKV; Window capture of the browser.
2. Record each shot as a clip, 3 takes each (checklist below).
3. Shotcut, Kdenlive or DaVinci Resolve (free): cut to timings, add cards, record VO.
4. Write `video/blindspot.srt`, one cue per VO line, for example:
   ```
   1
   00:00:00,000 --> 00:00:04,000
   Read raw, Punjab's fire record is off by {X%}.
   ```
5. Burn in via the editor or the ffmpeg `subtitles=` filter above.
6. Export H.264 + AAC; upload to YouTube, Public or Unlisted.
7. Real screen capture needs no watermark; add one for AI voice or images.

## 4. Checklists

**Capture:** PK Punjab preset selected; calendar raw; toggle click → harmonized with era shading; one hover tooltip; month card with "provisional"; CSV download. 1920×1080, light theme only, slow visible cursor, zoom so labels read at 1080p, no tabs/bookmarks/notifications/keys on screen.

**Subtitles:** English, word-for-word with VO; ≥28 px at 1080p with outline/box; bottom safe area; ≤2 lines × 42 chars; ≥1.2 s each; never over labels.

**Final QA:**
- [ ] `ffprobe -v error -show_entries format=duration -of csv=p=0 final.mp4` prints ≤30.0
- [ ] Numbers match results JSON (second person checks)
- [ ] Subtitles readable on a phone at arm's length
- [ ] Order rule followed
- [ ] Watermark present if needed
- [ ] No NASA logo
- [ ] Link plays logged out, private window, mobile data
- [ ] Music credit and AI statement on the project page

## 5. Fallback: 7 slides

1. Team names, challenge name
2. Blind Spot: harmonized fire calendar, Pakistan + northern India, 2003–today
3. Problem: raw record off by {X%}; sensor eras
4. Raw vs harmonized calendar (two screenshots side by side)
5. How it works: NASA FIRMS MODIS + VIIRS, calibration, T1/T2 ({STEP%})
6. For users: presets, month-vs-median card, CSV/PNG, link
7. Future impact: other regions, Urdu, NRT alerts; limits
