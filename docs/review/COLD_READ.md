# Cold read: submission and video script

Reviewer: a fresh Claude Code session (claude-opus-5-5, session `session_01APhUb4qrHD1BSYgL3hcuwE`) that had not seen the project. It got only the text of docs/SUBMISSION.md and docs/VIDEO_SCRIPT.md as generated on 31 Oct (Number sources tables left out) and was asked to read as a busy NASA judge. No subagent tool was available in this session, so a separate session stood in for the general-purpose subagent. Critique copied below; only list formatting in points 2, 6 and 7 of section 4 was reflowed.

---

# Judge's critique: Blind Spot

**Bottom line:** The method is solid and you're honest about its limits, which is rare. The main risks are a confound in your headline Indian Punjab finding and a summary written for someone who already knows the project.

## 1. Unclear

- **"afternoon counts miss"**: You never say that Aqua and S-NPP both pass over at about 13:30. Without that, a judge can't follow the argument.
- **"T1 is therefore judged on the 2012 step alone"**: T1 depends on the result of T2, so the tests read out of order. Use a small table instead: rows for each test, columns for Pakistan and India, cells for verdict and reason.
- **"S-NPP night share rose from 0.010% to 2.3%"**: Say what this is a share of. Also, 2.3% of detections at night can't explain 3,756 observed against 14,493 predicted. The night figure doesn't support the size of the claim.
- **"T2 found no drift in the 2 evaluable years" versus "each hour of overpass gap moves the ratio by +172%"**: Is there drift or not? These two lines read as contradicting each other.
- **"For each region and month"**: Which regions? You offer 347 districts and custom areas. Does each district get its own factor, or does it inherit a regional one? Districts with few fires will give unstable factors.

## 2. Overclaimed

- **"Our reading: farmers there burn later in the day."** This is the biggest validity risk. Aqua's orbit has been drifting to later crossing times since about 2022, and your own +172% per hour result shows the gap drives the ratio. If Aqua is passing later and catching more late fires, you would see Aqua/S-NPP rise even if farmer behaviour hadn't changed. Real burning in Punjab also fell in 2024–25 because of enforcement. You need to separate three explanations: orbit drift, a timing shift, and a real decline. If you can't, say all three are possible.
- **Video: "likely because fires burn later"**. The submission says "consistent with… does not prove". The video should use the same wording.
- **"Blind Spot fixes that for any district"**. You only tested two Punjab regions, and India fails after 2021.
- **"Method is global."** It is untested anywhere else. Say "the method should transfer" instead.
- **"rules written before we saw the results"** in the summary. Your Limits section admits the T2 rule was changed after you saw data. Put a short version of that admission in the summary too. A judge who finds it buried will trust everything else less.

## 3. Missing

- **Is +12.7% / −6.1% small?** Give the year-to-year spread from 2012–2021. If normal years vary by ±20%, say the remaining step is inside normal variation.
- **Pre-2012 check.** The factor was fit on 2012–2021 and then applied back to 2003. Show something supporting that, such as stable Terra/Aqua ratios over 2003–2011.
- **An outside check.** Compare against MCD64A1 burned area or official state stubble-fire counts. Even one correlation would help.
- **A named user and a use case.** Example: "A district officer in Ludhiana checks whether November 2025 is abnormal." Right now Impact is stated, not shown.
- **What NOAA-20 is used for** beyond "month card", and whether it is harmonized.
- **A screenshot** in the submission.
- **Prior work.** Name at least one existing MODIS–VIIRS harmonization paper, so "What is new" has something to be new against.

## 4. Scores as they stand, and fixes ranked by value

| Criterion | Score |
|---|---|
| Impact | 3 |
| Creativity | 4 |
| Validity | 3 |
| Relevance | 4 |
| Presentation | 3 |

1. **Address the Aqua orbit-drift confound** (Validity +1). Restrict to days with an overpass gap under 10 minutes, or model the gap explicitly, then restate the India conclusion based on what that shows.
2. **Rewrite the summary as three sentences** (Presentation +1, Relevance): the problem (the 2012 jump), the fix and its number, the honest caveat (the factor breaks after 2021 in India, cause unresolved). Move T1/T2 and the night-share figure out of the summary.
3. **Add a user scenario, plus one screenshot or GIF** of the raw→harmonized toggle (Impact +1).
4. **Add the year-to-year spread and a pre-2012 check** (Validity).
5. **Creativity:** Lead with your real novelty, a correction that reports when it stops working. Show a "factor not reliable after 2021" flag in the calendar UI and in the video. That is the memorable idea, and right now it's hidden.
6. **Video changes:** open on the jump itself (the raw chart), not a title card with a number on it; cut "98%" ("+613% to +13%" alone is clearer); swap the night-share chart for the calendar showing the post-2021 warning; at 68 words in about 26 seconds of speech the voice-over is rushed, cut to about 55 words; use the same caveat wording as the submission.
7. **Housekeeping:** fix "Coverage: Coverage:"; resolve the DOI notes (standard-archive VNP14IMGT and VJ114IMGT have their own DOIs); drop the 0.017% mask figure.

---

## Resolution (31 Oct)

Fixes went into the templates (`docs/templates/*.tmpl.md`); `make story` regenerated docs/SUBMISSION.md, docs/VIDEO_SCRIPT.md and docs/video/subtitles.srt. Every new number is a JSON placeholder.

| Point | Holds up? | Action |
|---|---|---|
| Overpass times not explained | Yes | T2 bullet now says both satellites cross in the early afternoon and Aqua's crossing drifted later. No crossing time typed in: t2.json has no official per-year table. |
| T1/T2 order hard to follow | Yes | Results now a table: T1a, T2, T1b, T1 overall per region, with the usable-year rule under it. |
| Night share unclear and too small | Yes | Defined as share of S-NPP window detections made at night; text now says it is far too small to explain the gap alone. Removed from the summary. |
| "No drift" vs "+172%/h" | Yes | Explained: matched days show no drift; the effect comes from days when Aqua passed later. Control region effect shown beside it. |
| Factors per district? | Yes | States the three calibration regions and that a district uses the factor of the region each detection falls in. |
| Orbit drift vs burning time vs less burning | Yes, main point | Claim "farmers burn later" removed. New "What we cannot separate" bullet names all three. The PLAN §2 pitch sentence (generated by `blindspot.pitch`, D-034) still says "burns later in the day"; it is no longer quoted in the submission. Changing the pitch logic is a team decision. |
| Video "likely" wording | Yes | Line now: "In Indian Punjab it fails after 2021, and the app says so." |
| "Fixes for any district" | Yes | Summary says what was tested; Limits adds "Tested in two regions". |
| "Method is global" | Partly | Removed from the submission and video end card. The app keeps it (CLAUDE.md rule 9 scope statement). |
| Post-data rule change missing from summary | Yes | Summary now says it. |
| Is the residual step small? | Yes | Added calibration-year scatter (sd of log residuals) from t1.json. |
| Pre-2012 check, outside check (MCD64A1) | Yes, not done | Listed under Limits. No time to run before the event. |
| User scenario | Yes | Added a hypothetical Ludhiana district-officer example. |
| NOAA-20 role | Yes | Splice step says NOAA-20 is raw-only plus the same-platform month card. |
| Screenshot | Yes | Paths to two existing screenshots added; embed images on the project page on 14 Nov. |
| Prior-work citation | Yes, not done | Needs a verified paper; open item for the team. |
| Novelty = correction that reports where it fails | Yes | "What is new" rewritten around it. A calendar flag for post-2021 Indian Punjab years is not built; listed under Limits. |
| Video: open on raw chart, cut 98%, ~55 words | Yes | Opens on the raw calendar with names over it; 98% cut; voice-over now 62 words (cut from 68; the 55 target would drop the closing call to action). |
| "Coverage: Coverage:", mask 0.017% | Yes | Both fixed. |
| Standard-archive DOIs | Open | Still marked "verify before submission"; the reviewer's claim that they differ is unverified too. |
| "Enforcement cut burning in 2024–25" | Not adopted as fact | We have no source in the repo; kept only as "less burning overall" among the three explanations. |
