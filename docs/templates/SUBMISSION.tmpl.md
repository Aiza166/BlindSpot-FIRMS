# Blind Spot: Space Apps 2026 project submission (draft)


**Pakistani Punjab's fire record jumps {{t1:results.hotspots.PK_Punjab.step_2012.raw_step|pct}} in the October–November burning season of 2012, when the record switches from MODIS to VIIRS; Blind Spot brings it to {{t1:results.hotspots.PK_Punjab.step_2012.harmonized_step|pct1}} and flags the years where it stops being comparable.**

## Project name

Blind Spot

## Challenge

Harmonization of MODIS and VIIRS Hot Spots

## High-level summary

When NASA's VIIRS sensor joined MODIS in 2012, the satellite fire record for Punjab jumped. Over the same fields and the same days (15 Oct–30 Nov 2012), S-NPP VIIRS counted {{t1:results.hotspots.PK_Punjab.step_2012.raw_step|pct}} against Aqua MODIS in Pakistan and {{t1:results.hotspots.IN_Punjab.step_2012.raw_step|pct}} in India. The jump coincides exactly with the sensor switch. Blind Spot puts NASA FIRMS MODIS and VIIRS detections on one VIIRS-equivalent scale; the jump falls to {{t1:results.hotspots.PK_Punjab.step_2012.harmonized_step|pct1}} (Pakistan) and {{t1:results.hotspots.IN_Punjab.step_2012.harmonized_step|pct1}} (India), within normal year-to-year spread. The app shows a burning calendar for any district in Pakistani and Indian Punjab and the area around them, {{index:period.first|year}}–{{index:period.last|year}}. From {{t3:t3.IN_Punjab.reliability|first_caution}} the record is less comparable: in Indian Punjab some burning moved past the afternoon satellites; those years are flagged.

We wrote the tests and thresholds before running them. We changed one T2 rule after seeing data and disclose it below, with both verdicts.

## Link to Project Demo

Video, 30 seconds or less, English subtitles: link added when uploaded. It opens with no login, password or permission.

## Link to Final Project

Live app: link added after the deploy (Cloudflare Pages).

Source code and data: https://github.com/Aiza166/BlindSpot-FIRMS

## Detailed description

### What it does

- Pick one of {{index:districts|len}} districts (geoBoundaries ADM2), a region preset, or draw a box or radius.
- See a calendar of burning with one cell per month and one row per year, raw or harmonized, with sensor eras shaded so you can see where the record changes.
- Compare a month with its usual level for that place, both with all years and with the years we flag left out.
- See the critical period of a district or region: the months in the top quarter of the year, with onset, peak and end (month level, not daily).
- Download the calendar or the filtered hotspots as CSV (up to {{constants:csv_row_cap|int}} rows), or the chart as PNG.

**Example: Sangrur (November {{usecase:sangrur.ym|year}}) and Kasur (November {{usecase:kasur.ym|year}}).** For each district we took the highest-burning November since 2012 in a year that is not on our caution list (rule fixed in `docs/DECISIONS.md` D-042 before choosing). A district officer in Sangrur (Indian Punjab) asks whether that November was unusual. The harmonized calendar shows {{usecase:sangrur.value|int}} S-NPP-equivalent hotspots against a {{usecase:sangrur.median_years.0}}–{{usecase:sangrur.median_years.1}} November median of {{usecase:sangrur.median|int}} ({{usecase:sangrur.ratio|x2}} the median, or {{usecase:sangrur.ratio_excl|x2}} against {{usecase:sangrur.median_excl|int}}, the median with the years we flag left out). NOAA-20, a second VIIRS satellite on the same afternoon orbit, saw {{usecase:sangrur.noaa20|int}} against its own {{usecase:sangrur.noaa20_years.0}}–{{usecase:sangrur.noaa20_years.1}} median of {{usecase:sangrur.noaa20_median|int}} ({{usecase:sangrur.noaa20_ratio|x2}}). Sangrur's {{usecase:sangrur.ym|year}} carries no caution flag, so the comparison stands. Across the border in Kasur (Pakistani Punjab), November {{usecase:kasur.ym|year}} shows {{usecase:kasur.value|int}} against a {{usecase:kasur.median_years.0}}–{{usecase:kasur.median_years.1}} median of {{usecase:kasur.median|int}} ({{usecase:kasur.ratio|x2}}, or {{usecase:kasur.ratio_excl|x2}} with the flagged years left out), with NOAA-20 at {{usecase:kasur.noaa20_ratio|x2}} its median; also unflagged.

**Contrast: November 2025, a flagged year.** The same districts in November {{usecase:sangrur25.ym|year}} look very different: Sangrur {{usecase:sangrur25.value|int}} hotspots ({{usecase:sangrur25.ratio|x2}} its median) and Kasur {{usecase:kasur25.value|int}} ({{usecase:kasur25.ratio|x2}}). Both years are on our caution list (Sangrur: Aqua's overpass drift and later burning; Kasur: Aqua's overpass drift), so the officer reads "far fewer fires seen at 13:30", not "far fewer fires". The app shows the caution banner and the flag in words.

![Explorer: year-by-month calendar in the cividis ramp, sensor eras shaded, flagged years marked with a caution triangle and striped year labels](screenshots/explorer-desktop-light.png)

![Use-case page: Sangrur and Kasur, highest-burning unflagged November, then November 2025 as a flagged contrast](screenshots/use-case-desktop-light.png)

![Sangrur calendar with the headline November in focus (no caution flag)](screenshots/usecase-sangrur-2.png)

![Sangrur calendar with November 2025 in focus: the year carries the caution flag, hovering shows the reason in words](screenshots/usecase-sangrur-flagged-2.png)

![Results page: T1, T2 and T3 verdicts for Pakistani and Indian Punjab](screenshots/results-desktop-light.png)

### How it meets the brief

| The challenge asks for | Blind Spot |
|---|---|
| Select an area of interest | District list ({{index:districts|len}} districts), region presets, or draw a box or radius on the map |
| Choose a date range | Start and end month controls; the calendar and CSV follow them |
| Calendar view, 2000s to present | Year-by-month calendar (one cell per month), {{index:period.first|year}}–{{index:period.last|year}} |
| Current month against the median | Month card: latest available month (labelled "not live"; the live current month appears when the near-real-time service is switched on at launch) against that place's median for the same month, with all years and excluding the years we flag, plus NOAA-20 against its own median |
| Critical periods | Panel per district and region: onset, peak and end month of the months in the top quarter of the year, and this year against typical; month level, not daily |
| Accessible colour ramps | Cividis (colour-vision-deficiency safe); flags shown by a triangle, stripes and text, not colour alone; axe-core found {{axe:runs|nviol}} violations across {{axe:runs|len}} runs (pages × light/dark × desktop/phone) |
| Download data | CSV of the calendar or of filtered hotspots (up to {{constants:csv_row_cap|int}} rows) |
| Download images | Chart as PNG |

### How it works

1. **Data.** FIRMS standard archive for MODIS (Terra, Aqua) and VIIRS (S-NPP, NOAA-20), clipped to {{constants:coverage_box.lon_min|int}}–{{constants:coverage_box.lon_max|int}}°E, {{constants:coverage_box.lat_min|int}}–{{constants:coverage_box.lat_max|int}}°N.
2. **Filters.** Vegetation fires only (`type` 0), MODIS confidence 30 or higher, VIIRS nominal or high confidence, dates in local solar time. A persistent-hotspot mask removes {{mask:n_masked_cells|int}} grid cells with year-round heat sources (kilns, flares) from every series.
3. **Calibration.** For each of {{calib:factors.Aqua->SNPP|len}} regions (Pakistani Punjab, Indian Punjab, and the rest of the study area) and each month we fit an Aqua MODIS to S-NPP VIIRS factor on 2012–2021 only, with a bootstrap by year. Example: Indian Punjab, October, {{t1:results.hotspots.IN_Punjab.heldout.factors_used.10|f3}}; Pakistani Punjab, October, {{t1:results.hotspots.PK_Punjab.heldout.factors_used.10|f3}}. Districts do not get factors of their own: each detection takes the factor of the calibration region it falls in, so a district with few fires inherits a stable regional factor. Districts also inherit that region's reliability flags; a drawn area takes the flags of every region it overlaps.
4. **Splice.** Before S-NPP, the series is Aqua times the factor; from S-NPP onward it is S-NPP as observed. We never add platforms together. NOAA-20 (from 2019) is not in the harmonized series. We use it for two things: a same-sensor check on the latest month (NOAA-20 against its own median, in the month card), and a stability test of S-NPP itself (below).
5. **Tests, fixed in advance** (window 15 Oct–30 Nov, Pakistani and Indian Punjab reported separately):
   - T1: the harmonized 2012 step must be under {{t1:parameters.step_threshold|upct}} of the raw step. Ratio: {{t1:results.hotspots.PK_Punjab.step_2012.ratio|f3}} (Pakistan), {{t1:results.hotspots.IN_Punjab.step_2012.ratio|f3}} (India). Both pass. Then, if T2 finds no drift, held-out years 2022–2025 must fall inside a {{t1:parameters.pi_level|upct}} prediction interval.
   - T2: does the Aqua/S-NPP ratio drift after 2021 once you control for overpass time? Both satellites cross in the early afternoon, but Aqua's crossing has drifted later in recent years. We compare only days when the two passed within {{t2:parameters.match_tolerance_h|min}} of each other.
   - T2b: VIIRS night share and the Terra/Aqua ratio by year, as a consistency check.
6. **App.** A static Next.js site. MapLibre draws the map; DuckDB-WASM reads Parquet hotspot tiles in your browser, so a custom area needs no server.

### Tools and languages

- Pipeline: Python 3.11 with DuckDB, pandas, PyArrow, SciPy and Shapely; Parquet files; pytest and ruff.
- Web app: TypeScript, Next.js 15 and React 19 as a static site, MapLibre GL JS for the map, DuckDB-WASM for queries in the browser, html-to-image for the PNG export.
- Hosting: Cloudflare Pages, with one Pages Function that fetches near-real-time FIRMS data so the key stays on the server.
- Checks: pytest, vitest, browser end-to-end tests (`web/e2e`), axe-core for accessibility.
- No hardware.
- Claude Code (Anthropic) wrote most of the code and tests under the team's direction; see "Use of Super Intelligence (SI)" below and the app's About page.

### Results, stated plainly

| Test | Pakistani Punjab | Indian Punjab |
|---|---|---|
| T1: does harmonizing remove the 2012 jump, and do 2022–2025 stay in the prediction interval? | **{{t2:t1_reevaluated.PK_Punjab.label}}**. Step ratio {{t1:results.hotspots.PK_Punjab.step_2012.ratio|f3}} (must be < {{t1:parameters.step_threshold|f2}}). | **{{t2:t1_reevaluated.IN_Punjab.label}}**. Step ratio {{t1:results.hotspots.IN_Punjab.step_2012.ratio|f3}} passes; only {{t1:results.hotspots.IN_Punjab.heldout.n_inside|int}} of {{t1:results.hotspots.IN_Punjab.heldout.n|int}} held-out years sit inside the {{t1:parameters.pi_level|upct}} interval. |
| T2: does the Aqua/S-NPP ratio drift after 2021 on days the two passed within {{t2:parameters.match_tolerance_h|min}}? | **{{t2:t2.PK_Punjab.verdict_revised.label}}**: {{t2:t2.PK_Punjab.verdict_revised.evaluable_test_years|len}} of {{t2:parameters.test_years|len}} test years have enough matched days. | **{{t2:t2.IN_Punjab.verdict_revised.label}}** on matched days ({{t2:t2.IN_Punjab.verdict_revised.evaluable_test_years|len}} of {{t2:parameters.test_years|len}} years usable); the failure comes from days Aqua passed later. |
| T3: why does it fail? O = Aqua's later overpass, T = burning moved later, D = less burning | O {{t3:t3.PK_Punjab.evidence.O.verdict}}, T {{t3:t3.PK_Punjab.evidence.T.verdict}}, D {{t3:t3.PK_Punjab.evidence.D.verdict}}. Flagged: {{t3:t3.PK_Punjab.reliability|caution}}. | O {{t3:t3.IN_Punjab.evidence.O.verdict}}, T {{t3:t3.IN_Punjab.evidence.T.verdict}}, D {{t3:t3.IN_Punjab.evidence.D.verdict}}. Flagged: {{t3:t3.IN_Punjab.reliability|caution}}. |

In short: the correction removes the 2012 jump in both regions; after 2021 it fails in Indian Punjab, is untested in Pakistani Punjab, and the app flags those years.

Both satellites cross Punjab in the early afternoon (about 13:30 local), but Aqua's crossing has drifted later in recent years. T1 judges held-out years only if T2 finds no drift, which is why T2 decides the second half of T1.

**Is the remaining 2012 step small?** The Aqua→S-NPP factor varies from year to year with a standard deviation of {{t3:t3.PK_Punjab.a4_factor_spread.sd_ln|f3}} (Pakistan) and {{t3:t3.IN_Punjab.a4_factor_spread.sd_ln|f3}} (India) in log units over {{t3:t3.PK_Punjab.a4_factor_spread.years.0}}–2021. The harmonized 2012 steps are {{t3:t3.PK_Punjab.a4_factor_spread.step_in_sd|f2}} and {{t3:t3.IN_Punjab.a4_factor_spread.step_in_sd|f2}} of those standard deviations: inside normal year-to-year spread.

**Does the factor hold before 2012?** We apply it back to 2003, where only MODIS exists. Terra and Aqua carry the same MODIS sensor at different times of day, so a trend in Terra/Aqua over 2003–2011 would warn that Aqua's view of burning was changing. Theil–Sen slopes: {{t3:t3.PK_Punjab.a5_terra_aqua_pre2012.theil_sen.slope_pct_per_year|pct1}} per year (Pakistan, CI {{t3:t3.PK_Punjab.a5_terra_aqua_pre2012.theil_sen.ci95_pct_per_year.0|pct1}} to {{t3:t3.PK_Punjab.a5_terra_aqua_pre2012.theil_sen.ci95_pct_per_year.1|pct1}}) and {{t3:t3.IN_Punjab.a5_terra_aqua_pre2012.theil_sen.slope_pct_per_year|pct1}} (India, {{t3:t3.IN_Punjab.a5_terra_aqua_pre2012.theil_sen.ci95_pct_per_year.0|pct1}} to {{t3:t3.IN_Punjab.a5_terra_aqua_pre2012.theil_sen.ci95_pct_per_year.1|pct1}}). Both intervals include zero, so we found no trend; India's upper bound sits close to zero, so a slow decline is possible.

**Is S-NPP itself stable?** NOAA-20 and S-NPP carry the same VIIRS instrument on the same afternoon orbit. Their ratio over 2019–2025 moved {{t3:t3.PK_Punjab.a1_noaa20_snpp.theil_sen.slope_pct_per_year|pct1}} per year in Pakistan and {{t3:t3.IN_Punjab.a1_noaa20_snpp.theil_sen.slope_pct_per_year|pct1}} in India (CIs include zero). A change in S-NPP counts after 2021 is therefore a change in what the afternoon orbit saw, not sensor decay.

**What T3 shows for Indian Punjab.** S-NPP daytime detections in the window changed {{t3:t3.IN_Punjab.a2_viirs_only.snpp_day_change_pct|pct}} in 2022–2025 against 2012–2021, while night detections rose {{t3:t3.IN_Punjab.a2_viirs_only.snpp_night_change_pct|pct}} and the night share went from at most {{t3:t3.IN_Punjab.a2_viirs_only.snpp_night_share_pre_max|upct1}} to {{t3:t3.IN_Punjab.a2_viirs_only.snpp_night_share_post_mean|upct1}}. A model of Aqua's overpass gap, fit on 2012–2017, leaves a {{t3:t3.IN_Punjab.a3_orbit_curve.post_residual_mean_pct|pct}} residual in Indian Punjab ({{t3:t3.PK_Punjab.a3_orbit_curve.post_residual_mean_pct|pct}} in Pakistan), so orbit drift alone does not explain India. Burning later (T) fits, and two geostationary studies report the same shift (Jethva/NASA Earth Observatory 2025; Singh et al. 2025). **We cannot separate T from D.** Night detections are about {{t3:t3.IN_Punjab.a2_viirs_only.snpp_night_share_post_mean|upct1}} of the total, so later burning alone may not account for the daytime fall; a real decline may also be present, and our data cannot size the two.

### Benefits

- Disaster and air-quality teams in Pakistan and India get a burning history for their own district that does not break in 2012.
- Researchers get a correction factor per region and month, with intervals. It passes the 2012 test in both regions; after 2021 it fails in Indian Punjab and is untested in Pakistani Punjab, and the app flags those years.
- You can download every series as CSV.

### What is new

Earlier work compared MODIS and VIIRS fire counts once and reported a ratio: Vadrevu and Lasko (2018) found VIIRS detected 6.5 times as many fires as Aqua in Indian Punjab; our factor for 2013–2018 in the 15 Oct–30 Nov window is {{t3:t3.IN_Punjab.a4_factor_spread.mean|f2}}. Separate studies found Punjab burning moved later in the day (Jethva 2025; Singh et al. 2025). Blind Spot joins the two: a correction that reports where it stops working. Each region-year carries a test result, and the calendar shows a flag with a plain-words reason on the years where the factor can no longer be trusted.

### What was built when

- **Before the hackathon (31 Oct to 2 Nov 2026):** the data pipeline, the tests T1 to T3 and a first version of the web app were prepared locally. Our team lead was told by the Universal Event Local Lead that local work, data download and a written plan were fine before the event.
- **During the hackathon (14 to 15 Nov 2026):** the changes recorded in `ai-log.md` and `decisions.md` in the repository, which was first published on 14 Nov.

### Limits (honest list)

- **Counts are an index.** A hotspot count tracks how much burning a satellite saw at its overpass times. It is not burned area, not fire numbers on the ground, and not emissions.
- **Pakistani Punjab T2 is inconclusive.** We cannot yet say whether the factor holds there after 2021.
- **Indian Punjab T1 fails** on the held-out years. The 2012 correction works; after 2021 the afternoon satellites miss fires lit later in the day, and we cannot tell how much burning also fell.
- **No independent check against non-FIRMS data yet.** We have not compared with official stubble-fire counts. We rejected MCD64A1 burned area: it picks its training pixels from MODIS active fires, so the check would be circular, and its grid cells are too coarse for small paddy fields. The 2003–2011 Terra/Aqua check is indirect.
- **Tested only in Punjab.** We chose Punjab because its post-monsoon stubble burning is dense and well studied, so a sensor jump shows clearly. The method uses only global FIRMS inputs, and it fits one factor per region and month, so extending it means drawing new calibration regions and rerunning the same tests there. We have not done that yet.
- **We changed the T2 verdict rule after seeing data** (minimum evaluable years, a control region). We logged the change and report the original verdict beside the revised one.
- **Near-real-time data is not live.** The month card shows the latest complete archive month, labelled "not live". Live NRT needs a server function we have not deployed.
- **Custom areas use simplified Punjab outlines.** For a test box on the border, {{aoi:months_differing_gt_0_1|int}} of {{aoi:months_compared|int}} months differed from the full pipeline, by at most {{aoi:max_rel_diff|upct1}}.
- **Coverage:** Pakistan and northern India only.

## NASA data used

| Product | What we used it for | DOI |
|---|---|---|
| MODIS Collection 6.1 active fire detections, MCD14ML (Terra, Aqua), via FIRMS | 2003 onward history; Aqua is the calibration base | doi:10.5067/FIRMS/MODIS/MCD14ML |
| VIIRS S-NPP 375 m active fire, VNP14IMG, via FIRMS | Reference scale, 2012 onward | doi:10.5067/VIIRS/VNP14IMG.002 (LP DAAC V002 record; FIRMS SP archive has no separate DOI found) |
| VIIRS NOAA-20 375 m active fire, VJ114IMG, via FIRMS | Second VIIRS series; month card | doi:10.5067/VIIRS/VJ114IMG.002 (LP DAAC V002 record; same note) |

Acknowledgement: "We acknowledge the use of data and imagery from LANCE FIRMS operated by NASA's Earth Science Data and Information System (ESDIS)."

## Space agency partner data and other references

No data from the 2026 Space Agency Partners. Other data:

| Data | Licence | Use |
|---|---|---|
| geoBoundaries gbOpen, Pakistan ADM1 and ADM2 | Public Domain | Regions, districts |
| geoBoundaries gbOpen, India ADM1 | CC BY 2.5 IN (DataMeet India) | Indian Punjab region |
| geoBoundaries gbOpen, India ADM2 | ODbL 1.0 (Pathways Data Pvt. Ltd.); our simplified `districts.geojson` is shared under ODbL 1.0 too | Districts |

Full licence text: the app's Attribution page and `web/public/data/ATTRIBUTION.md`.

Software, all open source: DuckDB and DuckDB-WASM (MIT), MapLibre GL JS (BSD-3-Clause), Next.js and React (MIT), pandas, SciPy and Shapely (BSD-3-Clause), PyArrow (Apache-2.0), marked and html-to-image (MIT), and the Instrument Sans and Newsreader fonts (SIL Open Font License) via Fontsource. The agent and skill files in `.claude/` are adapted from ECC (`.claude/ECC-ATTRIBUTION.md`). All screenshots are our own captures of the app. We used no copyrighted images or text from other sources.

## Use of Super Intelligence (SI)

We used Claude Code (Anthropic), including subagents, for:

- research (FIRMS formats, overpass times, licences),
- writing pipeline and web code and tests,
- code, security and accessibility reviews, and red-team critiques of the plan and results,
- first drafts of documents, including this one and the video script.

People on the team chose the research question, the scope, the pre-registered tests and thresholds, and approved each change. Every number in the app and in this text is read from pipeline output files by a script. We used no AI-generated images, video or voice. As the 2026 guide asks for code and data, SI use is also stated in the README, on the app's About page, and in the package metadata (`pyproject.toml`, `web/package.json`).

## References

- Giglio, L., Schroeder, W., Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. Remote Sensing of Environment 178, 31–41.
- Schroeder, W., Oliva, P., Giglio, L., Csiszar, I. A. (2014). The new VIIRS 375 m active fire detection data product. Remote Sensing of Environment 143, 85–96.
- Vadrevu, K., Lasko, K. (2018). Intercomparison of MODIS AQUA and VIIRS I-Band Fires and Emissions in an Agricultural Landscape. Remote Sensing 10(7), 978. doi:10.3390/rs10070978.
- NASA Earth Observatory (15 Dec 2025). New Timing for Stubble Burning in India (H. Jethva).
- Singh, N., Pradhan, R., Shukla, B. P., Pandya, M. R. (2025). Evidence of shift in stubble burning timing over northwest India from geostationary satellite observations. Current Science 129(10), 921–923.
- Runfola, D. et al. (2020). geoBoundaries: A global database of political administrative boundaries. PLoS ONE 15(4): e0231866.
- NASA FIRMS: https://earthdata.nasa.gov/firms
