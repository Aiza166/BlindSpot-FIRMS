# 05. Install OBS and practise a 30 s capture

**When:** before 13 Nov. **Time:** 45 min.

## What it is
Practice recording your screen with OBS Studio (free). The video is a ≤30 s screen capture with your voice and English subtitles (`docs/VIDEO_GUIDE.md`, Path B, the default).

## Why it matters
Presentation score: the video is currently not recorded (`docs/GRADE.md` item 1, the highest-ranked improvement). Practising now means launch day is faster.

## Steps
1. Download OBS Studio from https://obsproject.com/ and install it.
2. Settings: **Video**, base and output resolution 1920x1080, FPS 30. **Output**, recording format MKV (or MP4), then you can remux via **File, Remux Recordings**.
3. In **Sources**, click **+**, choose **Window Capture**, pick your browser window. Add **Audio Input Capture** for your microphone.
4. Open the local app (task 03, `npm run serve`, http://localhost:4173). Light theme, no bookmarks bar, no other tabs, no notifications visible, no keys on screen.
5. Click **Start Recording**, move the mouse slowly, click the raw/harmonized toggle, hover a calendar cell, **Stop Recording**. Files are saved under Videos by default.
6. Play it back: can you read the labels at 1080p? Is your voice clear?
7. Install a free editor to cut and add subtitles: Shotcut, Kdenlive or DaVinci Resolve. Install **ffmpeg** (needed for the duration check in task 09): https://ffmpeg.org/download.html, then `ffprobe -version` should work in PowerShell.

## Record the result
Tick the box. Keep practice clips out of the repo (large files).

## Common problems
- **Black window capture:** try **Display Capture** instead, or run OBS as administrator.
- **No audio:** check Windows Settings, Sound, Input; pick the right microphone in OBS.
- **Laggy:** lower to 1280x720 for practice only; the final should be 1080p.
- Rules about AI voice/images: `docs/VIDEO_GUIDE.md` section 1. Your own voice needs no AI watermark.
