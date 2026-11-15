# AI-assembled cut of the 30-second demo

`../blindspot_demo_ai.mp4` (29.97 s, 1920×1080, no sound) is a second version of the demo video, made by Claude Code on 15 Nov 2026 so the team can compare it with the manually recorded one.

- **Pictures:** real captures of the live app (https://blindspot-firms.pages.dev) taken with Playwright (`stills.mjs`, `stills2.mjs`); nothing in the app screens is redrawn.
- **Words:** the on-screen text and subtitles are the lines in `docs/VIDEO_SCRIPT.md`, unchanged. Long subtitle lines are split in time, not reworded.
- **Assembly:** `comp.html` lays out the stills, labels and subtitles as a function of time; `render.mjs full` captures 899 frames; ffmpeg encodes them.
- **No AI images or voice, no music.** A line at the bottom of every frame says the video was assembled with AI.

If this cut is submitted instead of the manual one, add it to the "Use of Super Intelligence (SI)" answer first.

Rebuild (needs Node, `npm i playwright`, `npx playwright install chromium`, ffmpeg):

    node stills.mjs && node stills2.mjs
    node render.mjs full
    ffmpeg -framerate 30 -i frames/f%04d.jpg -f lavfi -i anullsrc=r=48000:cl=stereo -shortest -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac blindspot_demo_ai.mp4
