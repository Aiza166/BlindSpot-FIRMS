# Video brief for Kissa's Claude Code session

Paste everything below the line into a new Claude Code chat opened in the `BlindSpot-FIRMS` folder on Kissa's PC. It assumes the session knows nothing.

---

You are helping me (Kissa) make the 30-second demo video for our NASA Space Apps 2026 project. Read this whole message before doing anything. Work in this repository; run `git pull` first.

## The situation

- **Project:** Blind Spot, a web app that puts NASA's MODIS and VIIRS fire detections on one scale and shows a burning calendar for any district in Pakistani and Indian Punjab. Challenge: "Harmonization of MODIS and VIIRS Hot Spots".
- **Team:** Aiza Gazyani and Kissa Zehra, team "Hehehehehe", Karachi Local Event.
- **Live app:** https://blindspot-firms.pages.dev
- **Repository:** https://github.com/Aiza166/BlindSpot-FIRMS
- **Deadline: tonight, Sunday 15 November 2026, 23:59 Karachi time (PKT).** The video must be uploaded and its link in the submission form before then. Aiza fills in the form. Aim to hand her the link by 22:30.
- **What I need from you:** help me record and finish a video with **my own voice** and a **real screen recording** of the live app. You cannot record or speak for me. You prepare everything, tell me exactly what to click and say, then cut, subtitle and check the file I record.

## Read these files first

1. `CLAUDE.md` (project rules; rule 7: every number comes from pipeline output files, never typed by hand).
2. `docs/VIDEO_SCRIPT.md` (the shot list, the voice-over, and the "Number sources" table). **This is the script. Do not rewrite it.**
3. `docs/video/subtitles.srt` (English subtitles, same words as the voice-over).
4. `docs/VIDEO_GUIDE.md` sections 1, 3b and 4 (hard rules, the manual recording path, checklists).
5. `docs/GUIDE_2026_NOTES.md` sections "Demo" and "Super Intelligence (SI) rules".
6. `YOUR_TASKS/09_record_video.md`.
7. `FIXES_FOR_KISSA.md` item 1 (the live current-month card is failing on the public site; this affects one shot, see below).

## Hard rules (breaking one can disqualify the project)

1. **Length 30.0 seconds or less.** Check with `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>`. Over 30 s is not eligible for Global Judging. Aim for 29.0 to 29.8 s.
2. **English**, with **English subtitles burned into the picture**, word for word with what I say.
3. **Order:** 0:00 our names and team name, then the challenge, the title, how it works with the real app and NASA data, and the last seconds on the future.
4. Team name "Hehehehehe", both members' names and the challenge name must be **shown on screen**.
5. **Numbers:** only these may be spoken or added as text: 2003, 2026, +613%, +12.7%, 2021, 1.74×, 1.94×, 2022 (the "Number sources" table in `docs/VIDEO_SCRIPT.md`). Numbers visible inside the real app screen are fine. Never invent or round a number.
6. Keep this sentence word for word: "From 2022, some burning moved past the afternoon satellites, so we flag those years." Do not say farmers burn later "because".
7. **No AI-generated voice, images or video.** My real voice and a real screen recording only. If you add anything AI-made, it needs a visible label and the submission's AI statement must change; avoid that.
8. No NASA logos, flags or mission badges. No person under 18 seen or heard. No copyrighted music; no music at all is fine.
9. Public link that opens with **no login**: YouTube, Public or Unlisted.
10. Never show a key, password, email inbox, browser tabs, bookmarks or notifications in the recording.

## The script (55 words, about 30 seconds)

> Aiza and Kissa, team Hehehehehe. Pakistani Punjab's October–November fire record jumps +613% in 2012, when sensors changed; Blind Spot brings it to +12.7%. Sangrur, November 2021: 1.74× its November median, checked against a second satellite. From 2022, some burning moved past the afternoon satellites, so we flag those years. Next: any farming region, same tests.

Say the numbers as "plus six hundred thirteen percent", "plus twelve point seven percent", "one point seven four times".

## Shots to record (real app, light theme, 1920×1080)

| Time | What to show | How to get there |
|---|---|---|
| 0:00–0:10 | First screen: "Start here: the 2012 jump" strip and the raw calendar for Punjab (Pakistan). Click **Harmonize the record**; the calendar changes | Open https://blindspot-firms.pages.dev and scroll so the strip and calendar are both visible |
| 0:10–0:20 | Sangrur, November 2021: 1.74× its November median, NOAA-20 1.94× | Open https://blindspot-firms.pages.dev/use-case/ and scroll to "Compare with a normal November" and "Check the same satellite on its own" |
| 0:20–0:27 | Sangrur calendar with the caution triangles; hover November 2025 so the reason shows | Open `https://blindspot-firms.pages.dev/?area=76128533B82601690264832&from=2003-01&to=2025-11`, scroll to the calendar, hover the November 2025 cell |
| 0:27–0:30 | End card: "Blind Spot", "Next: any farming region, same tests", `blindspot-firms.pages.dev`, our names and team | A plain title card you build (HTML page or the editor's title tool) |

**Do not show the "live current month" card as working.** On 15 Nov the public site's `/api/nrt` answers `504 "FIRMS did not answer in time"`, so the card shows the saved October month. Check it once before recording; show the live figure only if it really appears.

## What you should do, step by step

1. `git pull`, read the files above, and tell me in five lines what you understood and anything that looks wrong.
2. Check my tools: `ffmpeg -version`, `ffprobe -version`, and whether OBS Studio is installed. If something is missing, tell me how to install it; do not install anything without asking me.
3. Give me an **OBS setup checklist**: 1920×1080, 30 fps, MKV, window capture of one clean browser window (no tabs bar clutter, no bookmarks, 100% or 110% zoom, light theme, notifications off), microphone on, a test recording of 5 seconds that we check for sound.
4. Give me a **recording card**: for each shot, the URL, what to scroll to, what to click, and the exact words to say, with the target seconds. I will record each shot as its own clip, three takes each. Tell me to speak slightly slower than feels natural.
5. When I tell you where the clips are, **look at them** (extract frames with ffmpeg and read them), pick the best take of each, and cut them together with ffmpeg to the timings. Keep my voice as recorded; you may trim silence, normalise loudness to about -16 LUFS, and speed a clip up by at most 5% if we are over time. Never cut a word.
6. Add on screen: a top bar or lower third with "Aiza Gazyani and Kissa Zehra · Team Hehehehehe · NASA Space Apps 2026 · Harmonization of MODIS and VIIRS Hot Spots" for the whole video, the end card, and the subtitles from `docs/video/subtitles.srt` retimed to my actual speech (at most 2 lines, at least 36 px at 1080p, dark box behind white text, never covering the numbers being shown).
7. Export H.264 + AAC, yuv420p, `-movflags +faststart`, to `docs/video/blindspot_demo_final.mp4`.
8. **Verify and show me the evidence:** the `ffprobe` duration (must be 30.0 or less), `ffmpeg -af volumedetect` (voice audible, no clipping), and at least 8 frames you have looked at, including one from each shot. List every number that appears on screen or in speech and its row in the "Number sources" table.
9. Tell me to **watch it once with sound** and to upload it to YouTube as Unlisted or Public, then open the link in a private window to confirm it plays without login.
10. When I give you the YouTube link: put it in `docs/templates/SUBMISSION.tmpl.md` under "Link to Project Demo" (never edit `docs/SUBMISSION.md` by hand), run `make story`, then `python scripts/form_fields.py`, check that the "Use of Super Intelligence (SI)" text still says no AI video or voice was used (true for this video), add one row to `ai-log.md`, commit and push. Then tell me to send the link to Aiza. If `make story` fails for a missing file (`data/processed/harmonized/calibration_factors.parquet` exists only on Aiza's PC), stop and tell me; Aiza can run that step.

## If recording goes badly

Three finished AI-assembled cuts already exist as a fallback, all under 30 s:

- `docs/video/blindspot_demo_voice.mp4` (29.70 s, AI narration)
- `docs/video/blindspot_demo_brag.mp4` (29.27 s, silent, subtitles)
- `docs/video/blindspot_demo_ai.mp4` (29.97 s, silent, subtitles)

Each carries an "assembled with AI" line on every frame. If we must use one, the "Use of Super Intelligence (SI)" answer has to change first: say the demo video was assembled by Claude Code (brag, Hyperframes) from real screenshots of the app, and, for the voice cut, that the narration is AI-generated speech (Kokoro). Tell Aiza before doing this. If it is 22:15 and my recording is not finished and checked, say so plainly and recommend the fallback.

## How to work with me

- Plain words, short steps, one thing at a time. Tell me what you checked and what you could not check.
- Do not claim the video is fine until you have run the checks in step 8.
- Do not deploy, do not change app code, do not touch the FIRMS key.
- Small commits with clear messages; log the work in `ai-log.md`.
