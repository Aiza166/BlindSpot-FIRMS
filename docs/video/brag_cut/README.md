# Blind Spot demo, brag + Hyperframes cut

`../blindspot_demo_brag.mp4` is a third version of the 30-second demo, made by Claude Code on 15 Nov 2026 with the `brag` skill (v0.4.0, full workflow: `/brag --full --tone polished --no-sfx --no-music --title "Blind Spot"`) and rendered with Hyperframes.

- **Pictures:** real 2x Playwright captures of the live app (https://blindspot-firms.pages.dev), the same stills as `../ai_cut/stills/` (`assets/img/`). Nothing in the app screens is redrawn; the video only pans, zooms, crops and cross-dissolves them, and adds rings, a cursor, titles, cards and subtitles in HTML.
- **Words:** on-screen text and subtitles come from `docs/VIDEO_SCRIPT.md`. Subtitles are the voice-over, word for word, split in time (`compositions/captions.html`).
- **Sound:** none. The file carries a silent stereo AAC track (`assets/silence.wav`, generated with ffmpeg `anullsrc`) so players and upload forms accept it. No music, no SFX, no voice, no AI images.
- **Note on every frame:** "Real screens from the live app · video assembled with AI (Claude Code, brag, Hyperframes) · no AI images or voice".
- **Fonts:** the app uses Newsreader and Instrument Sans; the video uses Hyperframes' bundled EB Garamond and Inter as stand-ins.

If this cut is submitted, add it to the "Use of Super Intelligence (SI)" answer first.

## Files

| File | What |
|---|---|
| `brag-plan.md` | brag step 2: angle, storyboard, subtitle timing, guard rails |
| `composition-brief.md` | brag step 3: hand-off brief to Hyperframes |
| `composition/index.html` | root composition (29.25 s, 1920x1080, 30 fps), mounts the scenes |
| `composition/compositions/*.html` | `s-open`, `s-jump`, `s-sangrur`, `s-flag`, `s-end`, `chrome` (title bar and AI note), `captions` |
| `composition/assets/` | stills, silent WAV, vendored `gsap.min.js` 3.15.0 |
| `share-copy.txt` | one-paragraph caption |
| `poster.jpg` | the frame baked in as frame 0 (thumbnail) |

## Tools and versions

- Hyperframes CLI **0.9.52** (npm `hyperframes@0.9.52`), with its bundled `hyperframes` and `hyperframes-cli` skills; system Chrome for capture
- GSAP 3.15.0 (vendored)
- Node.js 24.3.0, FFmpeg/FFprobe 9.0.1 (gyan.dev build), Windows 11
- brag skill 0.4.0 (Claude Code plugin)

## Rebuild

From a scratch folder outside the repo (do not install into `web/`):

    npm i hyperframes@0.9.52
    cp -r <repo>/docs/video/brag_cut/composition ./composition
    cd composition
    npx hyperframes check
    npx hyperframes render --quality high -o ../brag.mp4
    cd ..
    # bake the poster as frame 0 (brag step 4) and make the delivery file
    ffmpeg -y -i brag.mp4 -i poster.jpg -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]" \
      -map "[v]" -map 0:a -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -r 30 \
      -c:a aac -b:a 128k -movflags +faststart blindspot_demo_brag.mp4
    ffprobe -v error -show_entries format=duration -of csv=p=0 blindspot_demo_brag.mp4   # must be <= 30.0

## Silent audio track

`composition/assets/silence.wav` (5.6 MB of digital silence) is not kept in git. Recreate it before rendering:

    ffmpeg -f lavfi -i anullsrc=r=48000:cl=stereo -t 30 composition/assets/silence.wav
