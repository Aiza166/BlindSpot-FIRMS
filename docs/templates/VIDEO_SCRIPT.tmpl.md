# Blind Spot: 30-second video script (draft)

Template: `docs/templates/VIDEO_SCRIPT.tmpl.md`. Regenerate with `make story`. Order follows docs/VIDEO_GUIDE.md: team names, challenge, title and tagline, how it works with NASA data, impact. Recording method: manual screen capture (VIDEO_GUIDE Path B); no AI images, video or voice. Subtitles: `docs/video/subtitles.srt` (same words as the voice-over).

## Shot list

| Time | Picture | On-screen text | Voice-over |
|---|---|---|---|
| 0:00–0:10 | Raw calendar, Pakistani Punjab, 2003–2025, the 2012 jump fills the frame; then click raw → harmonized, sensor eras shaded. Names and challenge in the lower third | {NAMES} · NASA Space Apps 2026 · Harmonization of MODIS and VIIRS Hot Spots · "2012 jump: {{t1:results.hotspots.PK_Punjab.step_2012.raw_step|pct}} → {{t1:results.hotspots.PK_Punjab.step_2012.harmonized_step|pct1}}" | <!--vo-->Pakistani Punjab's October–November fire record jumps {{t1:results.hotspots.PK_Punjab.step_2012.raw_step|pct}} in 2012, when the sensor changed; Blind Spot brings it to {{t1:results.hotspots.PK_Punjab.step_2012.harmonized_step|pct1}} and flags the years where it stops being comparable.<!--/vo--> |
| 0:10–0:20 | Month card for Sangrur, November {{usecase:sangrur.ym|year}} (highest unflagged November since 2012): value against its November median, NOAA-20 check beside it | "**Blind Spot** · Sangrur, {{usecase:sangrur.ym|year}}: {{usecase:sangrur.ratio|x2}} its November median · NOAA-20: {{usecase:sangrur.noaa20_ratio|x2}} · no caution flag" | <!--vo-->Sangrur, November {{usecase:sangrur.ym|year}}: {{usecase:sangrur.ratio|x2}} its November median, checked against a second satellite.<!--/vo--> |
| 0:20–0:30 | Sangrur calendar, November 2025 in focus: caution triangles, striped year labels, hover shows the reason; then end card | "From {{t3:t3.IN_Punjab.reliability|first_caution}}: less comparable, flagged" · Pakistan and northern India · app link | <!--vo-->From {{t3:t3.IN_Punjab.reliability|first_caution}}, some burning moved past the afternoon satellites, so we flag those years.<!--/vo--> |

## Voice-over (read straight through)

<!--vo-full-->

## Checks before recording

- Duration ≤ 30.0 s (`ffprobe`), voice-over ≤ 55 words (checked by `tests/test_story.py`). The 2026 guide: a demo over 30 s is not eligible for Global Judging (`docs/GUIDE_2026_NOTES.md`).
- The 2026 guide asks for the team name as well as member names at 0:00; add it to the lower third.
- No person under 18 may appear or be heard. No NASA logos in any generated card.
- A second person checks each on-screen number against "Number sources" below.
- Keep the caveat line word for word: it matches the submission summary. Do not say farmers burn later "because"; we cannot separate later burning from less burning.
