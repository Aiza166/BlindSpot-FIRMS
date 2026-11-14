# 09. Record the 30 s video

**When:** Sat 14 Nov, after the site is live (task 08). **Time:** 2-3 h.

## What it is
A ≤30 s screen recording with your voice-over and English subtitles, following `docs/VIDEO_SCRIPT.md` (53 words, 3 shots) and `docs/video/subtitles.srt`.

## Why it matters
Presentation score; the video is the first thing many judges see (`docs/GRADE.md` item 1).

## Steps
1. Re-read `docs/VIDEO_SCRIPT.md`. Check against task 07 whether the 2026 rules changed the length or format. If so, ask Claude to update the template and run `make story`.
2. Open the live site (or the local one) with the shots listed: raw 2012 jump then harmonized; Sangrur November 2021 month card; November 2025 flagged view. Do **not** say farmers burn later "because"; say what the script says.
3. Record with OBS (task 05), 1920x1080, 3 takes per shot. Record the voice-over by reading the script text straight through.
4. In the editor (Shotcut/Kdenlive/DaVinci Resolve) cut to the timings, add the cards, add subtitles from `docs/video/subtitles.srt` (or burn them with ffmpeg as in `docs/VIDEO_GUIDE.md`). Subtitles: ≥28 px at 1080p, bottom safe area, max 2 lines.
5. Export H.264 + AAC (MP4).
6. **Check the length:** `ffprobe -v error -show_entries format=duration -of csv=p=0 final.mp4` must print 30.0 or less.
7. Have a second person check each on-screen number against the "Number sources" table in `docs/VIDEO_SCRIPT.md`.
8. Upload to YouTube as **Public or Unlisted** (only after 14 Nov 09:00 PKT). Open the link in a private window to confirm it plays without login.
9. If you used music, credit it; if you used any AI image, video or voice, add the visible "AI-generated" watermark. Using your own voice and real screen capture needs neither. No altered NASA logos.

## Record the result
Put the video URL in `docs/CHECKPOINTS.md` (H34) and give it to Claude for the submission text.

## Common problems
- **Over 30 s:** trim pauses; do not speed up the voice.
- **Subtitles unreadable on a phone:** bigger font, add outline/box.
- **Fallback if the video fails:** ≤7 slides (VIDEO_GUIDE section 5), if the 2026 guide still allows it.
