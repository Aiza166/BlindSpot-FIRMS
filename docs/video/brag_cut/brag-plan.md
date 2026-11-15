# Brag Plan: Blind Spot

Invocation: `/brag --full --tone polished --no-sfx --no-music --title "Blind Spot"`

## What is this app?
Blind Spot is a harmonized MODIS + VIIRS fire calendar for Pakistan and northern India: it puts both sensor eras on one scale, so the 2012 sensor change stops looking like a burning boom, and it flags the years it can no longer check.

## The angle
A record that lies at one seam. The raw calendar for Pakistani Punjab "jumps" in 2012 only because the satellites changed. One click on the app's own "Harmonize the record" button and the jump shrinks from +613% to +12.7%. Everything after that is the app being honest: a real anomaly (Sangrur, November 2021) checked against a second satellite, and the later years it flags instead of hiding. The video is a NASA Space Apps 2026 demo, so the competition order is fixed: names and team, challenge, title, how it works, the future.

## Hook (first 2-3 seconds)
The team and the challenge, set calmly on the app's light grey paper: "Aiza Gazyani and Kissa Zehra", "Team Hehehehehe", "NASA Space Apps 2026", "Harmonization of MODIS and VIIRS Hot Spots". Then "Blind Spot" lands in the app's serif style and becomes the title bar that stays for the rest of the film.

## Key moments (the middle)
- The raw calendar (real screenshot) with the 2012 seam ringed: navy MODIS rows above, a different texture below.
- A cursor clicks the real "Harmonize the record" button; the story strip and the calendar cross-dissolve from raw to harmonized (both real screenshots), and the card "2012 jump: +613% → +12.7%" arrives.
- Sangrur, November 2021: the camera pushes into the bright yellow cell and its real tooltip, then the app's own paragraphs with 1.74× and the NOAA-20 1.94× check are marked; cards "Blind Spot · Sangrur, 2021: 1.74× its November median", "NOAA-20: 1.94×", "no caution flag".
- The caution flags: the camera moves to the triangles and the hover tooltip on the Sangrur calendar; card "From 2022: less comparable, flagged"; the app's "Caution years in this period" list slides in.

## Outro / punchline
"Next: any farming region, same tests." with the title, the link `blindspot-firms.pages.dev`, names, team and event. Silence.

## User flow worth showing
1. Entry: first screen, raw calendar for Punjab (Pakistan) 2003–2026 with the "Start here: the 2012 jump" strip.
2. Key action: click "Harmonize the record"; sensor eras rescaled.
3. Result: drill into one area (Sangrur) and one month (November 2021), then see the caution flags on later years with the hover reason.

## Tone
- Preset: polished
- Creative direction: quiet, factual science film; the app's own paper, ink and navy; no hype
- Interpretation: four content scenes plus an end card, long holds, slow push-ins and crossfades (0.6-0.8 s), one card per idea, mixed case, nothing loud. Text holds at least 0.5 s + 0.3 s per word.

## Format: landscape — 1920x1080, 30 fps
## Duration: 29.25 s (ffprobe 29.27 s) (competition limit 30.0 s; brag's 15-25 s default is overridden by the required script, which is 56 words and five mandatory lines)

## Visual identity (from the project, `web/app/globals.css`)
- Background: paper `#e8ecee`, sheet `#f5f7f8`
- Accent: `#284a6c` (app), title bar navy `#1f3550` (requested)
- Text: ink `#16212b`
- Warning: `#7a3b12`; focus/highlight `#b5531c`
- Display font: Newsreader (app) → EB Garamond in the video (bundled with Hyperframes; Newsreader files are not on this machine)
- Body font: Instrument Sans (app) → Inter in the video (bundled)
- Strongest visual element: the month × year calendar heatmap (shown only as real screenshots; never redrawn)

## Share copy (draft)
Blind Spot puts MODIS and VIIRS fire detections from 2003 to 2026 on one scale: Pakistani Punjab's +613% sensor-change jump becomes +12.7%. (Final wording in share-copy.txt; numbers limited to the approved list.)

## Audio direction
- Role: intentional silence (`--no-music --no-sfx`; bundled music licence unverified; no voice by competition rule)
- Music: none
- Music treatment: none
- Music cue guidance: not applicable (no music)
- Audio-reactive treatment: none
- SFX posture: none
- Audio-coupled moments: none; the click is shown visually (cursor press, button darkens)
- Restraint rule: the file carries a silent stereo AAC track only, so players and upload forms accept it

## Burned-in subtitles (voice-over words, word for word; split in time, never reworded)
| Time (s) | Text |
|---|---|
| 0.20–3.15 | Aiza and Kissa, team Hehehehehe. |
| 3.15–7.15 | Pakistani Punjab's October–November fire record jumps +613% in 2012, |
| 7.15–8.55 | when sensors changed; |
| 8.55–11.35 | Blind Spot brings it to +12.7%. |
| 11.35–14.95 | Sangrur, November 2021: 1.74× its November median, |
| 14.95–17.35 | checked against a second satellite. |
| 17.35–20.35 | From 2022, some burning moved past the afternoon satellites, |
| 20.35–22.55 | so we flag those years. |
| 22.95–29.05 | Next: any farming region, same tests. |

## Storyboard

### Scene 1 — Team, challenge, title — 0.0–4.75 s
Light paper ground. "NASA Space Apps 2026" small caps; "Aiza Gazyani and Kissa Zehra" word by word; "Team Hehehehehe"; "Challenge: Harmonization of MODIS and VIIRS Hot Spots" in a hairline card. At 3.2 s the block lifts away and "Blind Spot" lands large in serif ink; at 4.3 s it shrinks into the navy title bar that slides in and stays (bar carries names, team, event and challenge for the rest of the film).
Sequential/interaction: yes — names, team, event, challenge arrive one by one (each holds ≥ 1.2 s).
Audio intent: silence. Audio-coupled idea: none. Music: none.
Transition mood: carry across (title becomes the bar) → Scene 2

### Scene 2 — The 2012 jump — 4.75–11.4 s
Real screenshots: "Start here: the 2012 jump" strip (raw) above the raw calendar. Tag: "Raw record · Punjab (Pakistan) · 2003–2026". Camera pushes into the calendar; a ring marks the 2012 row with the label "MODIS gives way to VIIRS" (app wording). Camera pulls back to the strip; a cursor glides to "Harmonize the record" and presses it at 8.75 s; strip and calendar cross-dissolve to the harmonized screenshots, tag becomes "Harmonized · one scale for MODIS and VIIRS"; card "2012 jump: +613% → +12.7%" lands and holds.
Sequential/interaction: yes — simulated click on the real button.
Audio intent: silence. Transition mood: soft crossfade → Scene 3

### Scene 3 — Sangrur, November 2021 — 11.6–17.6 s
Real screenshots: the use-case heading, the Sangrur calendar with November 2021 focused (tooltip visible). Camera pushes into the yellow cell. The app paragraph "Compare with a normal November" slides in with "1.74×" marked, then "Check the same satellite on its own" with "1.94×" marked. Cards stack on the right: "Blind Spot · Sangrur, 2021: 1.74× its November median", "NOAA-20: 1.94×", "no caution flag".
Sequential/interaction: yes — three cards, each held ≥ 1.2 s, all held together at the end.
Audio intent: silence. Transition mood: soft crossfade → Scene 4

### Scene 4 — The flagged years — 17.6–22.9 s
Real screenshot: Sangrur calendar, November 2025 in focus, caution triangles and striped year labels, hover tooltip with the reason. Camera pushes to the lower right (triangles + tooltip). Card "From 2022: less comparable, flagged". The calendar steps back to the top right and the app's "Caution years in this period" list slides in at reading size, with the 2022 line ringed.
Audio intent: silence. Transition mood: soft crossfade → End

### Scene 5 — Next — 23.0–29.25 s
"Blind Spot" title, "Next: any farming region, same tests", link pill `blindspot-firms.pages.dev`, "Aiza Gazyani and Kissa Zehra · Team Hehehehehe · NASA Space Apps 2026", "Harmonization of MODIS and VIIRS Hot Spots", "Data: NASA FIRMS active fire detections (MODIS and VIIRS)". Holds dead still for the last 4 s.
Audio intent: silence.

Every frame: small note at the bottom, "Real screens from the live app · video assembled with AI (Claude Code, brag, Hyperframes) · no AI images or voice".

**Music mood for this video:** none (disabled)
**Audio summary:** a silent track for compatibility; the film is carried by picture and subtitles.

## Guard rails (competition)
- Numbers on screen: only 2003, 2026, +613%, +12.7%, 2021, 1.74×, 1.94×, 2022, plus numbers inside real screenshots, plus "2012" where the script's own words and on-screen text use it ("2012 jump", the voice-over subtitle).
- No redrawn charts or data. No NASA logos, flags or insignia. No people. No music, SFX or voice.
- Caveat line word for word; never "because".
