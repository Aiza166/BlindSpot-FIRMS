# Hyperframes Composition Brief: Blind Spot

## Objective
Create a 29.25 s NASA Space Apps 2026 demo video for Blind Spot, built as a Hyperframes composition from real screenshots of the live app plus HTML titles, labels, cards and subtitles.

## Output
- Composition directory: `composition/`
- Rendered video: `brag.mp4` (copied to the repo as `docs/video/blindspot_demo_brag.mp4`)
- Format: landscape — 1920x1080, 30 fps, H.264 + AAC (silent), yuv420p, faststart
- Duration: 29.25 s (hard limit 30.0 s)

## Source Material
- Project root: `hackathon/` (Next.js app in `web/`, live at https://blindspot-firms.pages.dev)
- Primary files read: `CLAUDE.md`, `docs/VIDEO_SCRIPT.md`, `docs/video/subtitles.srt`, `web/app/globals.css`, `web/app/layout.tsx`, `docs/video/ai_cut/` (capture scripts and stills)
- Product name: Blind Spot
- Strongest claim: Pakistani Punjab's raw 2012 jump of +613% becomes +12.7% when harmonized
- Key UI moments: "Start here: the 2012 jump" strip and its "Harmonize the record" button; the calendar heatmap (raw and harmonized); Sangrur use case paragraphs; caution triangles and hover reason
- Images (real 2x Playwright captures of the live app, `assets/img/`): `s1_story_raw`, `s1_story_h`, `s1_cal_raw`, `s1_cal_h`, `s2_head`, `s2_cal`, `s2_compare`, `s2_noaa`, `s3_cal`, `s3_notes`
- Copy that must appear verbatim:
  - Aiza Gazyani and Kissa Zehra · Team Hehehehehe · NASA Space Apps 2026 · Harmonization of MODIS and VIIRS Hot Spots
  - 2012 jump: +613% → +12.7%
  - Blind Spot · Sangrur, 2021: 1.74× its November median · NOAA-20: 1.94× · no caution flag
  - From 2022: less comparable, flagged
  - Next: any farming region, same tests
  - blindspot-firms.pages.dev
  - Real screens from the live app · video assembled with AI (Claude Code, brag, Hyperframes) · no AI images or voice
  - Subtitles: the voice-over of `docs/VIDEO_SCRIPT.md`, word for word, split in time (table in `brag-plan.md`)

## Creative Direction
- Tone preset: polished
- Creative direction: quiet, factual science film in the app's own paper/ink/navy
- Interpretation: few scenes, long holds, slow camera pushes on the screenshots, soft crossfades; titles land and stay still
- Angle: one click turns a fake fire boom into a flat record; then the app shows a real anomaly and its own caution flags
- Hook: names, team, event and challenge set on the app's paper; "Blind Spot" lands and becomes the title bar
- Outro: "Next: any farming region, same tests." + link
- Avoid: generic SaaS language; abstract filler; redrawn charts or invented numbers; click rings; bouncing UI; pulsing loops

## Visual Identity
- Background: `#e8ecee` (paper), cards `#f5f7f8` (sheet)
- Text: `#16212b`
- Accent: `#1f3550` navy bar and cards; app accent `#284a6c`; highlight `#b5531c`; warning `#7a3b12` on `#fff3e0`
- Display font: EB Garamond (stand-in for the app's Newsreader)
- Body font: Inter (stand-in for the app's Instrument Sans)
- Subtitles: Inter 600, 40 px, white on rgba(10,16,26,0.92) box, at most 2 lines, 50 px from bottom

## Storyboard
Use the storyboard in `brag-plan.md` as the creative contract.
1. Team, challenge, title — 4.75 s — names, team, event, challenge, "Blind Spot"
2. The 2012 jump — 6.6 s — raw → click → harmonized, card with +613% → +12.7%
3. Sangrur, November 2021 — 6.0 s — calendar push-in, paragraphs, three cards
4. The flagged years — 5.3 s — triangles, tooltip, caution list, warning card
5. Next — 6.25 s — end card with the link

## Audio
- Audio role: intentional silence (`--no-music --no-sfx`; competition forbids voice; music licence unverified)
- Music: none. SFX: none. Audio-reactive: none. Beat sync: not applicable.
- Audio files: `assets/silence.wav` (29.25 s digital silence, generated with ffmpeg `anullsrc`) placed as an `<audio>` clip so the MP4 has an AAC track.

## Hyperframes Instructions
Hyperframes 0.9.52 ships its domain guidance as two skills (`hyperframes`, `hyperframes-cli`) inside the npm package; the older split names (`hyperframes-core`, `-animation`, `-creative`, `-keyframes`) are folded into them. Follow that contract: root `index.html` mounting one sub-composition per scene from `compositions/`, a separate chrome overlay and a single captions host (`data-track-kind="captions"`), GSAP timelines registered on `window.__timelines`, `fromTo` tweens, local assets only (GSAP vendored in `assets/vendor/`).
- Show real UI only through the screenshots; HTML builds titles, labels, cards, cursor and subtitles.
- Keep every line readable; run `npx hyperframes check` as the gate; snapshot and look before rendering.
