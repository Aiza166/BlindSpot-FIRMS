# Blind Spot: project plan (v2, 31 Oct 2026)

v2 rewrites v1 after the red-team critique (`docs/CRITIQUE.md`, 2 FATAL + 8 MAJOR, all accepted or answered in §10). Markers: ✅ verified from a primary source · ⚠️ secondary or scheduled, re-check · ❓ unknown, owner must find out.

## 0. Rules that shape everything

| Item | Fact | Status |
|---|---|---|
| Pre-event work | Participant FAQ: **"Teams are not allowed to begin working on the challenges prior to the hackathon."** | ✅ quoted 31 Oct from spaceappschallenge.org/resources/participant-faqs |
| Build window | Submission opens Sat 14 Nov 09:00, closes Sun 15 Nov 23:59 in the Local Event's time zone; for the Universal Event, the Team Owner's local time (PKT if Aiza owns the team). The last saved submission is judged | ✅ 2026 hub, Universal Event page, 2026 Project Submission Guide |
| Team | Universal Event teams need ≥2 participants on the same team for global judging | ✅ Universal Event page |
| Local Lead | Chris, info@spaceappschallenge.org | ✅ |
| Official resources | Published Fri 13 Nov | ✅ challenge Resources tab |
| AI disclosure | Form field "Use of Super Intelligence (SI)" (not shown to judges). SI may not be used to come up with the idea. SI-generated code and data must be acknowledged in descriptive text and metadata; SI images and video need a visible watermark; no NASA branding in generated content | ✅ 2026 Project Submission Guide, read 14 Nov (`docs/GUIDE_2026_NOTES.md`) |
| Demo | ≤30 s video (English, or English subtitles) or ≤7 slides incl. title and intro; over either limit = not eligible for Global Judging. Public link, no login | ✅ 2026 Project Submission Guide, read 14 Nov |
| Form fields | Project Name; High-Level Project Summary; Link to Project Demo; Link to Final Project; Detailed Project Description; Use of SI; NASA Data (≥1 needed for a Global Award); Space Agency Partner Data and Other References | ✅ 2026 Project Submission Guide |
| Eligibility | All members confirmed at the same Local Event; all required fields; English only; no likeness of anyone under 18; tick Terms and "Confirm All Work is Original", then "Submit for Judging" | ✅ 2026 Project Submission Guide |
| Theme | "The Next Frontier" | ⚠️ team repos only |

**Update 31 Oct:** the team lead reports the Universal Event Local Lead said data download, a written plan and local work are fine for now (D-005). So: build locally, keep his written reply in `docs/evidence/`, and don't publish or deploy anything before 14 Nov 09:00. Every decision is logged in `docs/DECISIONS.md`.

## 1. What the challenge asks for (official, quoted)

1. Harmonize MODIS + VIIRS "so that ... the sensor of origin no longer matters".
2. "select a region and a specific date range, then download analytics and visualizations".
3. "A calendar of burning activity showing the number of hotspots detected from the early 2000s to the present": periods of the year, years, "how a current fire compares with previous ones".
4. "compare the burning activity of the current month against the historical median for a selected area".
5. "accessible color ramps".
6. "A downloadable CSV File of hot spots detected during a search".
7. Optional: draw the AOI or enter lat/lon; "anomalies against multi-year averages"; audience: emergency responders, scientists, land managers, firefighters.

## 2. The project

**Blind Spot**: a harmonized burning calendar for any district or drawn area in Pakistan and northern India, back to 2003, that shows where the satellite record itself has changed.

**Pitch (numbers filled from results JSON during the build):**
<!-- pitch:start -->
> "Blind Spot shows when this month's burning is unusual for any district. In Punjab's October–November season the raw fire record jumps +613% (Pakistan) and +371% (India) in 2012, when MODIS gives way to VIIRS; harmonized, +12.7% and -6.1%. Since 2022, some Indian Punjab burning moved past afternoon satellites; those years are flagged."

<sub>Numbers: `t1.json` results.hotspots.{PK,IN}_Punjab.step_2012.{raw_step,harmonized_step}. 'Removes that jump': `t2.json` t1_reevaluated.{PK,IN}_Punjab.step_pass. 'Moved later' clause needs `t3.json` t3.IN_Punjab.evidence.T.verdict == supported (D-039); this run: T=supported, D=cannot separate, clause=later. D-034 evidence (no longer a gate): night_share_rise=True, close_bin_ratio_rise=True, control_flat=True, supported=True. 52 words. Filled by `python -m blindspot.pitch` (`make t3`).</sub>
<!-- pitch:end -->

The before/after calendar toggle is the one visual. The method detail lives on the project page.

**Why this concept:** it meets every quoted requirement (Relevance), and adds one tested finding that competitor repos do not test (Validity, Creativity), framed around the user question "is this month unusual for my district?" (Impact). We say "we operationalise and test", never "first": the late-afternoon shift in Punjab burning is already reported publicly.

**Target awards:** Best Use of Science, Best Use of Data, Local Impact.

## 3. Data

| Dataset | Use | Access |
|---|---|---|
| FIRMS MODIS C6.1 standard (MCD14ML), Terra + Aqua | 2003–2011 history; overlap calibration | FIRMS yearly country CSVs (PAK, IND), fallback area API `MODIS_SP` |
| FIRMS VIIRS 375 m S-NPP standard (VNP14IMG), Jan 2012– | Reference scale | yearly country CSVs / `VIIRS_SNPP_SP` |
| FIRMS VIIRS NOAA-20 standard + NRT (VJ114IMG) | Continuity after S-NPP; current-month card | `VIIRS_NOAA20_SP` / `_NRT` |
| geoBoundaries ADM1 + ADM2 for PAK and IND | Fixed analysis regions; district presets | geoBoundaries (licence ❓ check) |
| Aqua/Terra mean local crossing time by year | Overpass control for T2 | NASA ESMO / Aqua status pages ❓ collect after 14 Nov |

Dropped from v1: MCD64A1 (circular with MODIS active fires, too coarse for paddy fields), NOAA-21 chain, OpenAQ.

Coverage box 60–80°E, 23–37°N. In-app scope line: "Coverage: Pakistan and northern India. The method should transfer to other regions."

## 4. Method (fixed before seeing data)

**Regions, fixed now:** PK Punjab and IN Punjab (geoBoundaries ADM1), reported separately. Season window for tests: 15 Oct–30 Nov.

**Filters:** standard data only for history; `type == 0`; MODIS confidence ≥30; VIIRS confidence n/h (robustness run with l/n/h); time converted to local solar time; persistent-hotspot mask (cell active in ≥3 years during Jan–Mar or Jul–Sep) applied to every series, NRT included.

> **Change log, 31 Oct 2026 (after seeing data, CLAUDE.md rule 6):** the mask rule above removed 52–68% of S-NPP detections in Jan–Mar and Jul–Sep, which include the forest-fire season and the start of paddy burning. It is replaced by a year-round rule: a 0.01° cell is masked when, in ≥3 distinct years, it has detections in ≥4 distinct months that cannot be covered by two 3-month windows. Reason and thresholds: `docs/DECISIONS.md` D-024. Both rules' results: `docs/MASK_COMPARISON.md`.

**Splice rule (the harmonized series):** VIIRS-S-NPP-equivalent hotspot scale.
- 2003–2011: Aqua MODIS counts × calibration factor.
- 2012–Oct 2026: S-NPP VIIRS as observed.
- After S-NPP ends: NOAA-20 × NOAA-20→S-NPP factor (fit on 2019–2025 overlap).

**Primary unit:** calibrated hotspot counts (the brief asks for "number of hotspots"). Robustness: fire cell-days on 0.05°, 0.1°, 0.25° grids, with the share of saturated cells reported per month.

**Calibration:** Aqua→S-NPP factor per region × month, fit on 2012–2021, bootstrap by year.

**Tests:**
- **T1 harmonization:** the 2012 step in the harmonized series is <10% of the raw step, and held-out 2022–2025 Aqua-predicted totals fall inside the 95% *prediction* interval. Conditional: T1's held-out part is judged only if T2 finds no drift.
- **T2 sensor consistency (overpass-controlled):** yearly Aqua/S-NPP ratio for each region, 15 Oct–30 Nov. Use only days where both observed the cell within 30 minutes of each other; regress the ratio on Δ crossing time. "Drift" = the 2022–2025 mean lies outside the prediction interval from 2012–2021, or the Theil–Sen trend CI excludes 0. Report the smallest drift detectable given 2012–21 variance. Report the separate effect "Aqua's crossing drift alone moves the ratio by X%".
- **T2b timing shift:** yearly VIIRS night (~01:30) share and Terra/Aqua ratio (crossing-time corrected) for 15 Oct–30 Nov. A rising night share is consistent with burning moving to hours the day passes miss. Claim consistency, not proof.
- **Mask report:** share of detections removed by the persistent-hotspot mask.

**Interpretation scripts (written now):**
- T2 drift: "Any calendar that uses Aqua at a fixed ratio after 2022 is biased by X%. Ours corrects it."
- T2 no drift: "The two sensors stayed consistent across 14 years; the harmonized record holds. Whether fires moved to unobserved hours is a separate question (T2b)."
- T2b rising: "The night share of detections rose from A% to B%, consistent with later burning that day passes miss; counts are an index, not a census."

## 5. Product scope

**Must:**
- AOI by district preset, drawn box, or lat/lon point + radius.
- Date range.
- Month × year calendar 2003–present, cividis ramp, values on hover, legend.
- Current month vs median card: NOAA-20 NRT vs NOAA-20 standard median (2019–), plus the harmonized median beside it, labelled "near-real-time, provisional".
- Raw vs harmonized toggle with sensor-era shading.
- CSV export of hotspots (capped at 200k rows with a "narrow your range" message) and of the calendar table.
- PNG export of the calendar and the card.
- Methods + limitations page, including the line that "current fire" is interpreted at month level.
- Results page (T1, T2, T2b, mask).
- AI-use statement.
- Project page and ≤30 s video.

**Should:** Urdu/English toggle; shareable AOI link.

**Cut:** chat agent, OpenAQ, MCD64A1, NOAA-21, forecasting, district comparison, global coverage.

## 6. Architecture (static-first)

- `pipeline/`: Python 3.11, DuckDB, pytest. Outputs: per-district JSON (calendar, medians, raw vs harmonized), partitioned Parquet (year × 1° tile) of masked hotspots, results JSON.
- `web/`: Next.js static export + MapLibre + DuckDB-WASM, querying the Parquet tiles in the browser for drawn boxes and CSV export. No always-on server.
- One serverless function for NRT (NOAA-20 last 30 days for the box). FIRMS key in host env only. If it fails, the card shows the last cached snapshot with its date.
- Hosting: Vercel or Cloudflare Pages ❓ decide at H0. Parquet tiles on the same static host or R2/GitHub Releases.

## 7. Before 14 Nov: allowed prep only (no project code, no project data)

| When | Task | Owner |
|---|---|---|
| Today | Email the Local Lead: (a) is downloading public NASA data before 14 Nov allowed? (b) is a written plan allowed? Keep the reply | Aiza |
| Today | Second member joins the same Universal Event team | Aiza |
| Today | FIRMS MAP_KEY + Earthdata login; test the key on the FIRMS site, not in code | Aiza |
| 1–5 Nov | Read the FIRMS FAQ, MCD14ML and VNP14IMG user guides, the FIRMS API docs | everyone |
| 1–5 Nov | Generic tooling: Node, Python, DuckDB, Claude Code + the `.claude/` harness, Vercel account | everyone |
| 6–10 Nov | Practise on unrelated public data (not FIRMS) if the team wants a warm-up | optional |
| 13 Nov | Read the official resources and the 2026 submission guide; update §0 | Aiza |
| 13 Nov | Name one person for video + submission; they stay off the code | Aiza |

If the Local Lead replies that downloads are allowed, the 13 Nov task list adds: request the FIRMS yearly country CSVs.

## 8. The 39-hour build (14 Nov 09:00 → 15 Nov 23:59 PKT)

| Hours | Pipeline / science | Web | Story |
|---|---|---|---|
| H0–H1 | Repo, Makefile, CI; download country CSVs | Next.js scaffold, deploy hello-world | Project page skeleton |
| H1–H6 | Ingest, filters, mask, counts + cell-days | Map + AOI picker on fake JSON matching the schema | Screenshots plan, script v1 |
| H6–H12 | Calibration, splice, T1; district JSON | Calendar + toggle on real JSON | — |
| H12–H20 | Sleep in shifts; T2, T2b, results JSON | Current-vs-median card, NRT function | — |
| H20–H26 | Parquet tiles | DuckDB-WASM box queries, CSV + PNG export | Fill pitch numbers from results JSON |
| H26–H30 | Code review, security review, fixes | Accessibility pass, phone test | Record video |
| H30–H34 | Freeze | Freeze | Edit video ≤30 s, subtitles, project page, AI statement |
| H34–H37 | Submit early, then smoke-test the public URL logged out | | |
| H37–H39 | Buffer | | |

Cut order if behind: Urdu → PNG export → T2b → drawn box (keep presets + lat/lon) → NRT live (use cached snapshot).

## 9. Checkpoints

See `docs/CHECKPOINTS.md`. Each gate is pass/fail with evidence and a score out of 10.

## 10. Critique response log

| # | Issue | Response |
|---|---|---|
| 1 | Rule breach | Accepted; verified the quote; §0, §7, §8 rebuilt |
| 2 | T2 confounded by Aqua drift | Accepted; overpass control + drift effect reported separately |
| 3 | T2 can't see behaviour shift | Accepted; T2b added; scripts reworded |
| 4 | Stats ill-posed | Accepted; prediction interval, Theil–Sen, fixed regions, window, splice, power |
| 5 | Cell-day saturation / wrong unit | Accepted; calibrated counts primary, multi-grid robustness |
| 6 | T3 circular | Accepted; cut |
| 7 | Critical path | Accepted; §8 |
| 8 | API fragility | Accepted; static-first + DuckDB-WASM, CSV cap |
| 9 | NRT vs standard mismatch | Accepted; NOAA-20 vs NOAA-20 median, mask on NRT, "provisional" |
| 10 | Pitch | Accepted; user-outcome pitch |
| 11 | Missing requirements | Accepted; PNG export, AI statement, month-level note, same-team check |
| 12 | Hygiene | Accepted; S-NPP date marked scheduled, "we test" not "first" |

**31 Oct 2026 post-data change (rule 6):** T2 verdict now also requires evaluable test years and adds a `rest_of_box` control; pitch logic changed. See `docs/DECISIONS.md` D-034. Both the D-033 and the revised verdict are reported.
