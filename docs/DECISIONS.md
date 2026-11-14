# Decisions

One entry per decision: what we chose, what we rejected, why, and the evidence. Newest last. Status: **Active**, **Superseded by D-xxx**, or **Revisit if** (a condition that would reopen it). Anyone (human or agent) who makes a non-trivial choice adds an entry here in the same commit.

---

## D-001 · Challenge: "Harmonization of MODIS and VIIRS Hot Spots"
- **Date:** 26–27 Oct 2026 · **Status:** Active
- **Chosen over:** Flame in Freefall (AI dashboard over microgravity combustion research); Be An Earth System Trend Detective; Field Shift (farms).
- **Why:**
  - **Data.** Free, clean, fast to get through NASA FIRMS. Flame in Freefall's data (PSI) is ~30 TB, mostly video, with broken legacy files.
  - **Validity.** The problem is a real scientific one, harmonizing two sensors, and rewards the lead's habit of auditing results.
  - **Local story.** Punjab crop burning and Lahore smog.
  - **Competition.** Flame in Freefall already had at least 8 near-identical "cited RAG" repos.
- **Evidence:** research report 1 scored A 7.6/10 vs B 6.6/10 on data access, skill fit, novelty, demo appeal and win potential.
- **Revisit if:** none; the challenge is locked.

## D-002 · Region: Pakistan and northern India, tests on PK Punjab and IN Punjab separately
- **Date:** 27–31 Oct · **Status:** Active
- **Chosen over:** global coverage; Pakistan only; India only.
- **Why:**
  - **Global loses on depth.** SHIFT (global) and FireLens (5 regions) already do breadth. We can't beat them on breadth in 39 hours.
  - **Pakistani Punjab is under-served.** Indian Punjab has official daily bulletins and the Stubble Fire Watch site. Pakistani Punjab has neither.
  - **Both, kept separate.** Covering both Punjabs gives a "one plain" story. Reporting them separately stops us picking the convenient one after seeing the data (critique #4b).
- **Revisit if:** official resources on 13 Nov point to a specific region.

## D-003 · Concept C: full brief-first product + one tested finding
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:**
  - (A) science-only "Blind Spot";
  - (B) product-only emergency-manager tool.
- **Why:**
  - **B alone** is what most of the 366+ teams will build, and Kiln Watch already runs it live.
  - **A alone** skips half the official asks (any AOI, date range, CSV, current vs median), which costs Relevance.
  - **C** meets every quoted requirement and adds a finding that no competitor repo we read tests.
- **Evidence:** official statement (`PLAN.md` §1); 11 competitor READMEs; 2023–2025 winners: "Best Use" awards went to validated analysis, and SpaceGenes+ won by surfacing one finding.
- **Revisit if:** the T2 result is null **and** the product is not ready by H26. Then cut T2 to a results-page note and put everything into product polish.

## D-004 · No arena tournament for the concept
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:** a 16-agent arena (91 sub-agent calls).
- **Why:**
  - **The decision was already constrained by evidence**: the brief, competitors and past winners.
  - **Cost.** A tournament spends hours re-deciding it.
  - **Cheaper alternative.** One red-team critic found 2 fatal issues for a fraction of the cost.
- **Revisit if:** we face a genuinely open design question with no evidence either way.

## D-005 · Pre-event work: build locally now, with Local Lead permission
- **Date:** 31 Oct · **Status:** Active
- **Context:** the Participant FAQ says "Teams are not allowed to begin working on the challenges prior to the hackathon" (verified). The team lead reports that the Universal Event Local Lead said downloading data, a written plan and working locally are fine for now.
- **Decision:**
  - Work locally.
  - **Keep the Local Lead's written reply** in `docs/evidence/` (not in git if it holds personal emails).
  - Don't publish or deploy before 14 Nov 09:00.
  - Push the repo only once the hackathon opens.
- **Why:** respects both the rule and the permission given; leaves an audit trail.
- **Revisit if:** the 2026 submission guide or the Local Lead says otherwise.

## D-006 · Primary unit: calibrated hotspot counts (VIIRS-S-NPP-equivalent); cell-days only as robustness
- **Date:** 31 Oct · **Status:** Active · **Supersedes:** v1 "cell-days on a 0.1° grid" as the primary unit
- **Why:**
  - **The brief's wording.** It asks for "the number of hotspots".
  - **Saturation.** 0.1° cell-days saturate in peak Punjab season, which squeezes the ratio toward 1 and biases T2 toward "no drift" (critique #5).
- **Robustness:** 0.05°/0.1°/0.25° cell-days, with the share of saturated cells reported.

## D-007 · T2 controls for overpass time; drift effect reported separately; T2b added
- **Date:** 31 Oct · **Status:** Active
- **Why:**
  - **Orbit drift.** Aqua stopped orbit maintenance around 2021–22, so a raw 2022–25 ratio change would measure orbit drift, not burning behaviour (critique #2).
  - **Same blind spot.** Aqua and VIIRS pass at nearly the same hour, so fires lit after the pass are lost from both and their ratio can't show it (critique #3).
  - **T2b** uses the VIIRS night share and the Terra/Aqua ratio. Those can show a timing shift, and we claim consistency, not proof.
- **Statistics:** prediction intervals (not a CI of the mean) and a Theil–Sen trend, with the smallest detectable drift stated.

## D-008 · Cut T3 (MCD64A1 burned area) and the burned-area panel
- **Date:** 31 Oct · **Status:** Active
- **Why:**
  - **Circular.** MCD64A1 uses MODIS active fires to pick its training pixels.
  - **Too coarse.** Its 500 m cells miss small paddy fields.
  - **Unsupported claim.** A falling counts/area ratio would not support "fires moved out of view" (critique #6).
- **Instead:** the limitations page names Sentinel-2/Landsat burned area as the independent check.

## D-009 · Static-first architecture: precomputed district JSON + Parquet tiles + DuckDB-WASM
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:** FastAPI + DuckDB on a free host.
- **Why:**
  - **Sleeping server.** Free hosts sleep, and the cold start can eat a 30 s demo.
  - **Unwatched.** Judges open links days later, with nobody watching the server.
  - **Large exports.** Unbounded CSV exports of large boxes run out of memory (critique #8).
  - **Static.** A static site has nothing to go down. Only near-real-time data needs one small serverless function.
- **Guardrail:** CSV capped at 200k rows, with a "narrow your range" message.

## D-010 · Current-month card compares NOAA-20 NRT with a NOAA-20 standard median
- **Date:** 31 Oct · **Status:** Active
- **Why:**
  - **No filter field.** NRT files lack the `type` filter field.
  - **No calibration.** NOAA-21 has no calibration against the long median.
  - **Fake anomalies.** Mixing products would show anomalies that aren't real (critique #9).
  - **Same platform.** Comparing NOAA-20 with NOAA-20 is consistent. The persistent-hotspot mask is applied to NRT too, and the card is labelled "near-real-time, provisional". The harmonized median is shown beside it.

## D-011 · Pitch leads with the user outcome and one number
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:** "the exchange rate drifted".
- **Why:**
  - **Audience.** The challenge writes for emergency managers.
  - **Time.** A 30 s video can't teach a metaphor and show a product (critique #10).
- **Form:** "Read raw, Punjab's fire record is off by X%. Blind Spot corrects it for any district, back to 2003." X comes from results JSON only. We say "we test", never "first".

## D-012 · Cut: chat agent, OpenAQ smog panel, NOAA-21, forecasting, district comparison
- **Date:** 31 Oct · **Status:** Active
- **Why:**
  - **Chat agent.** Kiln Watch already ships one that blocks unsupported numbers, so it no longer sets us apart.
  - **OpenAQ.** The US Consulate Lahore feed may have stopped in Feb 2025.
  - **The rest.** NOAA-21 and the other items don't fit 39 hours.
- **Revisit if:** everything Must is done by H26. Then the chat is the first add-back, because it plays to the lead's MCP strength.

## D-013 · Claude Code harness: copy 13 selected ECC files into `.claude/`; no installer, no hooks
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:** running ECC's `install.sh`; the full 314-skill profile.
- **Why:**
  - **Global writes.** The installer writes to the global `~/.claude`, and its hooks run on every tool call.
  - **Known bugs.** The repo's own roadmap lists bugs in one skill.
- **Safety edits:**
  - Each copied file was read for hidden instructions first.
  - We removed a cache-wipe that ran without confirmation.
  - Session notes moved out of global settings into the project.
- **Attribution:** `.claude/ECC-ATTRIBUTION.md` (MIT).

## D-014 · Data access: FIRMS yearly country CSVs first; MAP_KEY API for near-real-time and top-ups
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:** the area API for history; the emailed archive request.
- **Why:**
  - **Country CSVs** are standard-processing data, need no login, and give a whole country-year per file.
  - **The API** returns at most 5 days per call, so a 23-year history means thousands of calls.
  - **Archive requests** are queued.
- **The MAP_KEY is still needed** for the near-real-time "current month" card.
- **Note:** this cloud workspace's network policy blocks `firms.modaps.eosdis.nasa.gov`, so the data download runs on the lead's own machine (or after the host is allowed in the environment settings).
- **Revisit if:** a country file is missing a year or a platform.

## D-015 · Continuity after S-NPP: NOAA-20 calibrated to S-NPP on the 2019–2025 overlap
- **Date:** 31 Oct · **Status:** Active
- **Data-start conflict:** the FIRMS archive page says NOAA-20 375 m runs from 1 Apr 2018; the FIRMS FAQ says 1 Jan 2020 (see docs/DATA_SCHEMA.md). The fit uses only years present in the downloaded files; QC reports the first NOAA-20 date.
- **Why:** FIRMS states that S-NPP delivery ceased on 2 Nov 2026 and tells users to move to NOAA-20/21. NOAA-20 has standard data from April 2018, which gives an overlap long enough to fit the factor. NOAA-21 only starts in March 2023 (FIRMS archive page).

## D-016 · The product must be able to win without the T2 finding
- **Date:** 31 Oct · **Status:** Active
- **Why:** T2 may come back null. Build order puts every Must product feature (calendar, current vs median, AOI, CSV/PNG export, accessibility) ahead of T2/T2b polish. T2 is the headline if it lands, never a crutch.

## D-017 · Work split: lead builds everything now; teammate polishes later
- **Date:** 31 Oct · **Status:** Active
- **Why:** the teammate is busy until the hackathon. The lead preps and builds locally so the project is complete without her; she then improves design, copy and the video. Nothing on the critical path depends on her.

## D-018 · A real user quote is optional, sought through low-effort channels
- **Date:** 31 Oct · **Status:** Active
- **Why:** a quote from a real user helped QUEÑARIS win Local Impact, but the lead has no direct contact. Send one short message to 3–5 reachable people (see the outreach note in the chat log / OUTREACH.md if created). Never invent, paraphrase into stronger words, or attribute a quote without written consent. If nobody answers by 13 Nov, drop it.

## D-019 · Video: manual screen capture is the default; brag is optional
- **Date:** 31 Oct · **Status:** Active
- **Chosen over:** brag (latent-spaces/brag, MIT) as the main path.
- **Why:**
  - **It rebuilds instead of recording.** brag recreates the UI as an HTML animation from the source code, so it can show a UI or numbers that differ from the live app. That is a Validity risk.
  - **AI watermark.** Its output counts as AI-generated video, which needs a visible watermark for the whole video.
  - **Length and subtitles.** It caps at 25 s and has no subtitles.
  - **Recording the real app** shows exactly what judges will click.
- **Revisit if:** we want a short animated intro shot; brag can make that one shot, watermarked. Guide: `docs/VIDEO_GUIDE.md`.

## D-020 · Ingest: filters are flag columns, nothing is dropped; duplicates flagged in DuckDB
- **Date:** 31 Oct 2026 · **Status:** Active
- **Chosen over:** dropping rows while reading; one combined `keep` column.
- **What:**
  - Each PLAN §4 filter is its own boolean column: `passes_standard` (version has no NRT/RT/URT suffix), `passes_type` (`type == 0`; False when the file has no `type`), `passes_conf`, `passes_conf_robust`, `in_box` (60–80°E, 23–37°N, edges inclusive).
  - `hotspots_filtered` (DuckDB) and `ingest.filtered_view` (pandas) combine them. QC counts each step.
  - Duplicates (same platform, UTC time, lat, lon) are flagged `is_duplicate` in the `hotspots` view, keeping the first by file name and row, and excluded from `hotspots_filtered`.
  - `hotspots_filtered_nrt` drops the type filter because NRT has no `type` (D-010); the persistent-hotspot mask does that job for NRT.
  - Local solar time is stored as a naive timestamp (it is not a civil time zone). Partitions use the UTC year.
- **Why:** filters must be testable and countable one by one (QC, mask report), and a later robustness run must not need a re-ingest.
- **Revisit if:** files are too large to hold one at a time in memory (switch the per-file read to DuckDB `read_csv`).

## D-021 · Confidence classes and robustness flag
- **Date:** 31 Oct 2026 · **Status:** Active
- **What:** MODIS class low < 30 ≤ nominal < 80 ≤ high; `passes_conf` = confidence ≥ 30 (PLAN §4). VIIRS `l/n/h` and spelled-out `low/nominal/high` both accepted; `passes_conf` = n/h; `passes_conf_robust` = l/n/h. For MODIS, robust = primary (PLAN names a robustness run for VIIRS only). Unparsable confidence → class null, fails both.
- **Evidence:** docs/DATA_SCHEMA.md §5 (boundary 80 is from the MODIS user guide, marked ⚠️).

## D-022 · Persistent-hotspot mask: 0.01° grid, one static mask from all platforms, share per platform
- **Date:** 31 Oct 2026 · **Status:** Cell-selection rule superseded by D-024; grid, pooling and per-platform reporting still Active (set before any data was seen)
- **Chosen over:** a 0.004° (~400 m) grid; per-platform masks; separate year counts for Jan–Mar and Jul–Sep.
- **What:**
  - Grid 0.01° (≈1.1 km N–S, ≈0.96 km E–W at 30°N), configurable (`--grid`).
  - A cell is masked when it has a `hotspots_filtered` detection in ≥3 distinct years, counting months Jan–Mar and Jul–Sep together (a year counts if either window is active), with months and years taken from local solar time.
  - Detections from all platforms build one static cell list, applied to every series and every year, NRT included.
  - The share removed is reported per platform only (CLAUDE.md rule 1).
- **Why:**
  - **400 m is finer than MODIS.** A MODIS pixel is 1 km at nadir and grows toward the scan edge, and its centre moves from orbit to orbit. A kiln seen by MODIS lands in many different 400 m cells, so it would rarely reach 3 years in one cell. The mask would remove static sources from VIIRS but not from MODIS, which biases the Aqua/S-NPP ratio that T2 tests. At ~1 km, MODIS repeat detections of one source mostly share a cell.
  - **One static mask** keeps the same ground excluded in every era, so the 2012 splice does not change what is masked.
  - **Combined windows** follow the plain reading of PLAN §4 ("≥3 years during Jan–Mar or Jul–Sep").
- **Cost:** a 1 km cell is about 7 VIIRS pixels, so a field next to a kiln is masked too. The mask report shows how much this removes; a 0.004° run is one flag (`--grid 0.004`) if a robustness check is wanted.
- **Revisit if:** the mask report shows a very different share removed for Aqua and S-NPP over 2012–2021. That would mean the mask itself acts differently by sensor. Log any change in PLAN.md with the date, and report both.

## D-023 · Downloader: stdlib HTTP, configurable country-file URL, conservative API budget
- **Date:** 31 Oct 2026 · **Status:** Active
- **Chosen over:** `requests`/`httpx` (an extra dependency for one GET loop); a hard-coded URL.
- **What:**
  - `urllib` behind a small transport function, so tests mock HTTP without network.
  - Resume with HTTP Range on `.part` files; skip valid existing files; exponential backoff from 2 s, honouring `Retry-After`.
  - 404 is recorded as `not_found` and not retried. A body that is not a CSV header (e.g. an HTML error page) is `invalid_content` and is not kept.
  - The yearly-country URL pattern is unverified (DATA_SCHEMA.md §3), so it is a setting, and the CLI exits 2 with instructions if nothing downloads.
  - Area API: key read only from `FIRMS_MAP_KEY` in the environment; it is never logged, and the key is removed from errors and left out of the NRT manifest. `DAY_RANGE` is capped at 5. A sliding budget of 4000 day-transactions per 10 minutes (the reported limit is 5000) and a ≥1 s gap between calls.
- **Revisit if:** FIRMS publishes the country-file URL pattern, or the key's status page shows a different limit.

## D-024 · Persistent-hotspot mask: year-round persistence replaces off-season recurrence (supersedes the cell-selection rule of D-022)
- **Date:** 31 Oct 2026 · **Status:** Active. **Changed after seeing data** (CLAUDE.md rule 6): the old rule's removal shares were measured on real FIRMS data before this entry was written. The new rule and its thresholds below were fixed before the new rule was run on real data. Both rules' numbers are reported in `docs/MASK_COMPARISON.md`; the old rule stays runnable (`--rule seasonal-offseason`) for that comparison only.
- **Kept from D-022:** 0.01° grid, `hotspots_filtered` detections from all platforms pooled into one static cell list, applied to every series and year (NRT included), months/years in local solar time, share removed reported per platform only. FIRMS `type == 2` (static land source) is still removed upstream by `passes_type`.
- **Chosen over:** D-022's rule ("≥3 distinct years with a detection in Jan–Mar or Jul–Sep"); the lead's draft ("≥4 distinct months in a year, not all within one 3-month window").
- **What (new rule, `--rule year-round`, default):**
  - A **cell-year** is *year-round* when the cell has detections in **≥4 distinct calendar months** of that year **and** those months **cannot be covered by any two windows of 3 consecutive months** (windows wrap Dec→Jan).
  - A cell is **masked** when it has **≥3 distinct years** that are year-round (years need not be consecutive). All detections in a masked cell are removed, as before.
  - Thresholds: `min_years = 3`, `min_months = 4`, `season_len = 3` months, `max_seasons = 2`.
- **Why:**
  - **The old rule deletes real fires.** Jan–Mar is the start of northern India's forest-fire season and Punjab paddy burning starts in mid/late September, so recurrence in those months is seasonal burning, not a static source. The lead measured S-NPP removal of 52–68% of detections in Jan–Mar and Jul–Sep under the old rule.
  - **Static sources are active across the year, not in one season.** Kilns, steel plants and flares are seen in many months, spread over more than one season. The test is therefore spread across the calendar, not activity in a chosen set of months.
  - **Two windows, not one.** The draft's second clause ("not all within one 3-month window") can never bind once ≥4 months are required, because a 3-month window holds at most 3 months. More importantly, a 1 km cell in a rice–wheat field burns in two seasons every year (wheat Apr–May, paddy Oct–Nov): that is 4 distinct months and would be masked by the draft. Requiring the months to escape any two 3-month seasons keeps double-cropped fields, and a forest cell that also holds a field, unmasked.
  - **≥4 months as well.** Three isolated months (e.g. Jan, May, Sep) escape two windows but are too few to call year-round.
- **Cost / known blind spots:** a source active in only 4–6 months that fit two seasons (e.g. a kiln seen only Jan–Mar and May) is no longer masked. A forest cell whose fire season runs 5+ months and that also burns in a second season could be masked. `docs/MASK_COMPARISON.md` lists the 10 masked cells with most detections, by coordinates, for a human to check on imagery.
- **Revisit if:** the imagery check finds the top masked cells are fields or forest, or the comparison shows a very different share removed for Aqua and S-NPP over 2012–2021 (D-022's condition still applies). Log any change here and in PLAN.md with the date, and report both.

## D-025 · Regions: geoBoundaries gbOpen (release commit 4004e96), shapely STRtree point-in-polygon, derived coordinate→region table
- **Date:** 31 Oct 2026 · **Status:** Active
- **Source:** geoBoundaries gbOpen ADM1 + ADM2 for PAK and IND. The official index `releaseData/geoBoundariesOpen-meta.csv` (raw.githubusercontent.com, non-LFS) gives, per boundary set, the licence, source and a static download link pinned to repo commit `4004e96`. The downloader (`blindspot.boundaries`) reads that index, picks the row whose `boundaryID` starts with `{ISO}-{ADM}-` (the index also holds a mislabelled `IND-ADM0-…` row typed ADM1, which is skipped), and fetches `geoBoundaries-{ISO}-{ADM}.geojson` from the same commit. Licence and source go into `data/raw/boundaries/manifest.json` and `docs/DATA_SCHEMA.md` §8.
- **Regions:** PK Punjab = the PAK ADM1 feature whose `shapeName` is "Punjab"; IN Punjab = the IND ADM1 feature whose `shapeName` is "Punjab" (case- and space-insensitive; anything other than exactly one match is an error). shapeIDs are written by `make regions` to `data/processed/regions/regions.json`. Third pooled region for the app: `rest_of_box` = in the coverage box and in neither Punjab.
- **Library:** shapely 2 `STRtree.query(points, predicate="intersects")` (vectorised, a pip wheel). Rejected: DuckDB `spatial` (an extension downloaded at run time from extensions.duckdb.org, which this workspace cannot reach, and one more moving part); geopandas (pulls pyproj/GDAL stack for one join).
- **Join:** `intersects`, so a point on a shared edge is not lost. The derived table `data/processed/regions/point_regions.parquet` is keyed by the exact (lat, lon) of each filtered detection, long format (`level`, `shape_iso`, `shape_id`); raw hotspot partitions are not rewritten. geoBoundaries draws each country as it represents itself, so PAK and IND polygons can overlap (Kashmir) or leave slivers along the border; a point inside two countries' polygons gets a row for each, and `regions.json` reports how many points fall in both Punjabs.
- **Districts:** an ADM2 district series is harmonized with the factor of the calibration region of each detection, using that district's own country (PAK district point in PK Punjab → PK Punjab factor, else `rest_of_box`; same for IND), so no detection is counted twice inside one district series.
- **Known limitation:** PAK gbOpen is Wikipedia-derived and coarse (mean 600 vertices per ADM1 unit, per the index), IND ADM1 is DataMeet 2011. Points near the international border can fall in a gap or overlap.

## D-026 · Local solar date for day/month/year everywhere downstream of ingest; platform-day availability
- **Date:** 31 Oct 2026 · **Status:** Active
- **What:** every day, month and year in calibration, splice, T1 and the harmonized series is taken from `CAST(local_solar_datetime AS DATE)`. The UTC `year` partition is used only to read files. This fixes the 31 Dec boundary noted at H6 (a detection at 22:00 UTC on 31 Dec at 75°E is on 1 Jan local).
- **Availability:** a platform is *available* on a local date when it has at least one standard-processing, in-box row that day (any type or confidence, before the mask). Calibration and T1 compare two platforms only on their **common available days**, so a gap in one record (e.g. S-NPP before 20 Jan 2012, MODIS outages) does not bias the ratio. The harmonized series uses all days of its source platform and stores `days_available / days_in_month`; months below 90% are flagged `partial`.
- **Cost:** a day on which a platform truly saw nothing in the whole box counts as unavailable; in Oct–Nov that does not happen in this box, and the number of excluded days is reported.

## D-027 · Calibration estimator, bootstrap, splice details
- **Date:** 31 Oct 2026 · **Status:** Active (fixed before any calibration was run)
- **Factor:** per region × calendar month, `f = Σ_y S-NPP_y / Σ_y Aqua_y` over years 2012–2021 (ratio of totals over common days). Rejected: mean of yearly ratios (unstable when a year's Aqua count is small); regression through the origin (weights years by Aqua², dominated by peak years).
- **Uncertainty:** bootstrap by year — resample the 10 calibration years with replacement, B = 2000, seed 20261114 (`numpy.random.default_rng`), 2.5/97.5 percentiles. A factor is not defined when Σ Aqua = 0 (stored as null; the harmonized value is then null, never zero).
- **Splice (PLAN §4):** months 2003-01…2011-12: Aqua × f(region, month); 2012-01…2026-10: S-NPP as observed; after 2026-10: NOAA-20 × g(region, month). Jan 2012 is S-NPP even though S-NPP starts 20 Jan (flagged `partial`). Platforms are never added: each harmonized month has exactly one `source_platform`.
- **NOAA-20 → S-NPP factor g:** same estimator, fit on the years 2019–2025 named in PLAN §4, intersected with the years present in the files. NOAA-20 standard data in our files start 1 Apr 2018 (QC); 2018 is present but left out because PLAN §4 fixes 2019–2025 and 2018 is a partial year. g is computed and stored now; it feeds no month yet because the files end in Dec 2025, before the S-NPP cut-over.
- **Raw per-platform series** (Terra, Aqua, S-NPP, NOAA-20, each alone) are written beside the harmonized one.

## D-028 · T1 definitions (written before T1 was computed)
- **Date:** 31 Oct 2026 · **Status:** Active. Written before any T1 number existed (rule 6).
- **Common to both parts:** regions PK Punjab and IN Punjab, each alone; window 15 Oct–30 Nov by local solar date; common available Aqua/S-NPP days only; Aqua-predicted total `P_y = Σ_m f_m · Aqua_{y,m}` with the full-calendar-month factors for October and November (the same factors the harmonized series uses).
- **2012 step (part a).** At the splice the record switches from Aqua to S-NPP. The step is measured on the same fires, in the 2012 window, where both sensors observed:
  - raw step = `S_2012 / A_2012 − 1` (the jump a reader of the raw record sees when Aqua is replaced by S-NPP);
  - harmonized step = `S_2012 / P_2012 − 1`, where P uses factors fit on **2013–2021 only** (2012 left out, so the test is not in-sample);
  - pass if `|harmonized step| / |raw step| < 0.10`. Interval: the same ratio over B = 2000 year-bootstrap draws of the 2013–2021 factors (seed 20261114); the verdict uses the point estimate.
- **Held-out part (b).** For each calibration year y (2012–2021), residual `e_y = ln(S_y / P_y^(−y))` with factors fit on the other nine years. 95% prediction interval for one new year: `mean(e) ± t_{0.975, n−1} · sd(e) · √(1 + 1/n)`. For each held-out year 2022–2025, `e_y = ln(S_y / P_y)` with factors fit on all of 2012–2021; inside if it lies in the interval. Part (b) passes if all four held-out years are inside. Reported as observed vs predicted with the interval on the count scale.
- **Verdict:** T1 passes for a region when (a) and (b) both pass. Because PLAN §4 says (b) is judged only if T2 finds no drift and T2 is not run yet, every T1 verdict is labelled **"provisional pending T2"**.
- **Robustness (not a verdict):** the same (a) and (b) on fire cell-days at 0.05°, 0.1°, 0.25°, with their own factors.

## D-029 · Cell-day robustness unit and "saturated cell" share
- **Date:** 31 Oct 2026 · **Status:** Active
- **Cell-day:** a (grid cell, local date) with ≥ 1 masked, filtered detection of that platform in the region; grid index `floor(coord / grid + 1e-9)` as in `mask.py`. Grids 0.05°, 0.1°, 0.25°.
- **Saturated share** (critique #5 wording, "cells with both sensors active"): per region × grid × year-month, over common Aqua/S-NPP days, `cell-days where both Aqua and S-NPP are active / cell-days where either is active`. Written per year-month to Parquet; the JSON gives each calendar month pooled over 2012–2021.

## D-030 · Boundaries could not be fetched in the analyst workspace (H12 blocked on data, not code)
- **Date:** 31 Oct 2026 · **Status:** Open
- **What happened:** every geoBoundaries geometry file (current `main`, v5.0.0, v6.0.0, and the 2.0.1/3.0.0/4.0.0 archive repos) is a Git LFS pointer on raw.githubusercontent.com. The LFS content hosts (media.githubusercontent.com, the github.com LFS batch API) and www.geoboundaries.org are refused by this workspace's egress proxy; only the non-LFS index CSV came through. No third-party copy was used: provenance and licence must be the official files.
- **Consequence:** the code for regions, calibration, splice and T1 is written and tested on synthetic fixtures, and runs from one command (`make boundaries regions calibrate t1`, all inside `make data`), but `t1.json` has not been produced on real data here. Run `make boundaries` on a machine that can reach GitHub LFS (any normal connection), then `make regions calibrate t1`.

## D-031 · Reminder: Indian ADM2 district boundaries are ODbL 1.0 (share-alike)
- **Date:** 31 Oct · **Status:** Active, must be handled at web-app build time
- **Note:** if the web app redistributes the Indian district polygons, attribute geoBoundaries/source and keep the derived boundary data under ODbL. PAK ADM1/ADM2 is Public Domain; IND ADM1 is CC BY 2.5 IN (attribution).

## D-032 · H12 verification notes: border overlap and the 12 Nov 2025 S-NPP outage
- **Date:** 31 Oct · **Status:** Active
- **Border overlap:** 9,539 points (0.2%) lie inside both the PAK and IND Punjab ADM1 polygons, because the two files come from different sources. They are counted in both regions. That is acceptable because the regions are tested separately and never summed. The app must not add PK + IN Punjab totals. **Revisit if** a combined "both Punjabs" total is ever shown.
- **Common-day rule confirmed:** S-NPP has no data on 12 Nov 2025 (local solar date). T1 drops that day for Aqua too. This exactly explains the gap between t1.json Aqua 2025 and a naive recount (PK 1,994 − 27 = 1,967; IN 2,909 − 95 = 2,814).
- **Independent spot-check (own shapely point-in-polygon, own filters):** PK 2012 Aqua 770 and S-NPP 5,491; PK 2025 S-NPP 11,189; IN 2012 Aqua 13,178 and S-NPP 62,057; IN 2025 S-NPP 3,756. All match t1.json exactly.
- **Boundary fetch:** `boundaries.py` now requests geometry from media.githubusercontent.com (Git LFS host), same official repo and pinned commit. The t1.json run was made with this change uncommitted; it is committed together with these results.

## D-033 · T2 and T2b definitions; source of equator-crossing times (written before any T2/T2b number was computed)
- **Date:** 31 Oct 2026 · **Status:** Active. Written before T2/T2b were run (rule 6).
- **Crossing-time source.** Official NASA pages give milestones only, no per-year table: Aqua completed its last 13:30 MLT maneuvers in Dec 2021, began free drift in Jan 2022 and "exceeded a 1:45 PM MLT crossing in February 2023" (MODIS Land Team, https://modis-land.gsfc.nasa.gov/news.html; NASA Earthdata "Aqua Turns 20", https://www.earthdata.nasa.gov/news/feature-articles/aqua-turns-20; Aqua status, https://assets.science.nasa.gov/content/dam/science/missions/aqua/AquaStatus_May2024.pdf). Terra's last inclination maneuver was 27 Feb 2020; it drifts earlier from 10:30 toward 10:15 MLT (same MODIS Land page; Earthdata "From Terra to Terra Firma"). **No official per-year table was found**, so overpass time is derived empirically: for each region × local date × platform, the *scene time* = median local solar time-of-day of that platform's daytime (`daynight = 'D'`) masked, filtered detections; the yearly overpass time = median of the scene times over the window's days. Reported for Aqua, Terra, S-NPP, NOAA-20. This is the time fires were seen over the region, not the equator-crossing MLT (VIIRS's wide swath spreads it by up to about ±1 h day to day).
- **Common to T2/T2b:** regions PK Punjab and IN Punjab, each alone; window 15 Oct–30 Nov by local solar date; same mask, filters and common-available-day rule as T1 (D-026). Daytime detections only for every ratio (Aqua's and S-NPP's afternoon passes are what drift; night passes are T2b).
- **T2 ratio.** `r_y = Σ Aqua_D / Σ S-NPP_D` over the year's **matched days**: common days on which both platforms have daytime detections in the region and `|scene time Aqua − scene time S-NPP| ≤ 30 min` (PLAN §4 "both observed within 30 minutes"). The region-level scene time is used instead of per-cell matching because FIRMS only records detections, not non-fire observations, so "observed the cell" cannot be known for a cell without a fire; the region (≤ ~6° wide) is covered by one daytime pass of each sensor. The unmatched ratio over all common days is reported beside it (not a verdict).
- **Drift rule (PLAN §4), on `ln r_y` of matched days:** (i) 2012–2021 gives n = 10 values with mean m, sd s; the 95% prediction interval for the mean of the 4 new years is `m ± t_{0.975, n−1} · s · √(1/n + 1/4)`; drift if the 2022–2025 mean lies outside; or (ii) Theil–Sen slope of `ln r_y` on year over 2012–2025 (`scipy.stats.theilslopes`, 95%) has a CI excluding 0. Drift if (i) or (ii). A year with no matched day is dropped and reported.
- **Aqua-drift effect.** OLS over 2012–2025 of `ln r_y^all` (all common days, so the drift is not removed by the matching) on `Δ_y` = yearly median of daily (Aqua − S-NPP) scene time in hours. Effect = `exp(b) − 1` % per hour (95% CI from the OLS t interval); implied effect for each year = `exp(b · (Δ_y − mean Δ_{2012–21})) − 1`. Also reported: the drift test (i) on the overpass-adjusted `ln r_y^all − b(Δ_y − mean Δ_{2012–21})` — b is fit on all years, so this is descriptive, not a test.
- **Minimum detectable drift:** `exp((z_{0.975} + z_{0.80}) · s · √(1/10 + 1/4)) − 1` on the matched ratio, s = 2012–21 sd of `ln r_y`.
- **T2b.** (1) Night share per year 2012–2025 = night / (day + night) detections in the window on that platform's available days, S-NPP and NOAA-20 (2019+) each alone. (2) Terra/Aqua ratio by year 2003–2025 = Σ Terra_D / Σ Aqua_D on common Terra/Aqua days; **crossing correction:** Aqua counts are adjusted by the T2 Aqua-drift coefficient, `ln(T/A)_corr = ln(T/A) + b · (Δ_y − mean Δ_{2012–21})` (Aqua's own drift only, years ≥ 2012 where Δ exists; earlier years uncorrected). Terra's earlier drift is not corrected (no independent estimate); its scene time is reported beside it. Claim consistency, never proof.
- **Mask report:** platform shares from `mask_report.json` plus, per region, share of window detections (all years) removed by the mask, per platform.
- **T1 re-evaluation (PLAN §4):** if T2 finds drift in a region, T1's held-out part is "not judged (T2 drift)" and T1 for that region rests on the 2012 step only; if no drift, the held-out result stands.
- **Rejected:** per-cell 30-min matching (non-fire observations unknown); using MLT from TLEs (not an official per-year NASA table, and it adds an external dependency).

## D-034 · Post-data changes to the T2 verdict, a control region, and the pitch logic (CLAUDE.md rule 6)
- **Date:** 31 Oct 2026 · **Status:** Active. **Written after T2 results were seen** (red-team, `docs/CRITIQUE_RESULTS.md`), before recomputing. The D-033 verdict stays in `t2.json` and in every table beside the revised one.
- **(a) Evaluable test years.** A test year (2022–2025) enters the revised T2 verdict only if (1) it has **≥ 10 matched days**, and (2) its all-days median Δ(Aqua − S-NPP) is within the 30-min tolerance. Justification: every 2012–2021 year has 18–23 matched days in both regions, so 10 is about half the calibration-period minimum; below it one or two days drive the year's ratio (PK 2025: 3 days, 41 Aqua fires). Rule (2): once the typical Δ exceeds the tolerance, matched days are a selected tail (days when S-NPP fires clustered late), not a like-for-like sample (critique #5). Years failing either rule are labelled "insufficient". **Revised verdict:** fewer than 2 evaluable test years → **inconclusive**; otherwise the D-033 rules (PI on the mean of evaluable test years; Theil–Sen over 2012–2021 plus evaluable test years) → **drift** / **no drift**.
- **(b)** The "overpass-adjusted ratio back inside the range" result is circular (b is fit on all years, and Δ is ~0 before 2022, so b absorbs any post-2022 change; critique #4). It stays in `t2.json` as descriptive only and is used by no verdict and no pitch clause.
- **(c) Control region.** `rest_of_box` (the calibration box outside both Punjabs; same Aqua drift, different burning behaviour) is run through the same T2/T2b code and shown in every T2/T2b table, labelled "control, post hoc". It has no pre-registered verdict.
- **(d) T1 label.** If the revised T2 is "drift" or "inconclusive", T1 is "pass (2012 step only; held-out not judged: T2 {label})"; held-out is judged only on "no drift" (unchanged PLAN §4 logic).
- **Pitch "moved later" clause** is used only if all hold: IN S-NPP night share 2022–25 mean > 2012–21 max; IN ratio in the close-overpass bins (|Δ| ≤ 0.5 h) is higher in 2022–25 than 2012–21; control all-days 2022–25 mean inside its 2012–21 prediction interval. Otherwise a neutral clause.
- **Rejected:** dropping the D-033 verdict (rule 6 needs both); a 5-day minimum (still one-day-dominated).

## D-035 · Static app data layout (`make appdata`)
- **Date:** 31 Oct · **Status:** Active
- **What:** `pipeline/blindspot/appdata.py` writes `web/public/data/` from existing outputs only (harmonized/monthly_*.parquet, hotspots + mask, boundaries, results JSON). 347 ADM2 districts (every ADM2 with area in the coverage box, same set as `monthly_harmonized`), 3 calibration regions.
- **Series end:** last month of the harmonized grid after dropping trailing partial months (<90% days, `calibrate.PARTIAL_COVERAGE`); currently 2025-12 (2026-01 has 1 local-solar day).
- **Medians:** per calendar month over complete (non-partial, defined) months. Harmonized baseline 2003 → last full year; per platform from its first full year (Terra/Aqua 2003, S-NPP 2012, NOAA-20 2019 per D-010, not its Apr 2018 start) → last full year. Baseline years and `n_years` are stored in each file. Rejected: a 2012–2021 baseline (would drop the MODIS-scaled history the calendar exists to show).
- **Raw per platform:** four separate arrays, `null` where the platform had no available days; no field holds a cross-platform sum (rule 1; enforced by `validate_area_doc`). CALIB regions overlap at the border (D-032); the app must not add PK + IN files.
- **ADM1 of a district:** ADM1 of the same country containing the district's representative point; nearest same-country ADM1 when the sources disagree.
- **Boundaries:** one `districts.geojson`, shapely `simplify(0.01°, preserve_topology)`, coords rounded to 3 dp → 0.48 MB (target < 3 MB). Feature properties carry licence + attribution; IND ADM2 derived boundaries are ODbL 1.0 (D-031).
- **Tiles:** 1° × 1° by floor(lat/lon) (box upper edge folded in), local solar year, zstd, double lat/lon/frp (float32 showed digits like 3.8099999 in CSV), `acq_date` date32. 4.75 M rows, ~105 MB, under the 300 MB budget, so no column was dropped. CSV cap 200,000 (D-009) in `tiles/manifest.json` and `constants.json`.
- **Git:** `web/public/data/*` is ignored except `index.json`, `constants.json`, `ATTRIBUTION.md`, `results/`. Districts, regions, GeoJSON and tiles are regenerated by `make appdata`. Rejected: committing districts (7 MB, churns on every rerun).
- **FIRMS DOIs:** not previously in DATA_SCHEMA; taken from the citation strings FIRMS publishes (MCD14ML `10.5067/FIRMS/MODIS/MCD14ML`; VNP14IMGT `10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002`; VJ114IMGT `10.5067/FIRMS/VIIRS/VJ114IMGT_NRT.002`) and added to DATA_SCHEMA §9. Revisit if FIRMS lists separate DOIs for the standard (SP) archive.

## D-036 · Custom-AOI harmonized series computed in the browser (`results/calibration.json`)
- **Date:** 31 Oct · **Status:** Active
- **What:** `make appdata` now also writes `web/public/data/results/calibration.json`: Aqua→S-NPP and NOAA-20→S-NPP factors (unit hotspots, per region × month, with bootstrap lo/hi), the splice months (`snpp_first`, `snpp_last`), per-platform days available per month, and the PK and IN Punjab ADM1 outlines simplified at 0.0005° (5 dp). For a drawn box or point + radius the browser reads the tiles with DuckDB-WASM, counts each platform separately (never summed), and applies the D-027 splice: before 2012 each Aqua detection is scaled by the factor of its calibration region (inside PK Punjab → PK_Punjab, else inside IN Punjab → IN_Punjab, else rest_of_box); from 2012 S-NPP as observed. Partial months and medians use the same rules as `appdata.monthly_median`; baseline years are copied from `regions/rest_of_box.json`.
- **Differences from the pipeline:** the pipeline assigns a detection's region from the shape's own country; a custom box has no country, so PK is tested first. Points in the 0.2% border overlap (D-032) and within the simplification tolerance can get the other factor.
- **Evidence:** `web/e2e/check_custom_aoi.py` recomputes the box 74.4–75.2 E, 30.9–31.6 N (straddles the border) in Python with the original polygons and `calibration_factors.parquet`: Aqua counts identical in all months; 1 of 83 Aqua-era months differs (2.3 hotspots, 4.7%). With the map outlines (0.01°) 24 months differed by up to 31%, hence the finer outline.
- **Rejected:** raw-only for custom AOIs (loses the product's point); district-of-centroid factor (wrong across the border); shipping unsimplified outlines (larger, no measurable gain).
- **Browser budget:** a custom AOI whose tiles hold more than 2.5 M rows is refused with "draw a smaller box"; districts and the two Punjab regions use the precomputed JSON.

## D-037 · Web app stack and offline choices (A4)
- **Date:** 31 Oct · **Status:** Active
- **Stack:** Next.js 15.5 App Router, `output: 'export'`, TypeScript strict; MapLibre GL 5 with an inline style (background + `districts.geojson`), no basemap tiles and no key; fonts self-hosted from @fontsource (Newsreader, Instrument Sans). Results/Methods/About/Attribution pages are rendered at build time from `public/data` (Python's `-Infinity` in t2.json is mapped to null when read).
- **DuckDB-WASM pinned to 1.28.0:** 1.29–1.32 load the Parquet extension from extensions.duckdb.org at runtime, which is blocked here and would make the static site depend on a third-party host. 1.28.0 has Parquet (zstd) built in. Bundles are copied from node_modules into `public/duckdb/` at build. Tiles are fetched whole (≤ ~0.8 MB each) and registered as buffers, so no HTTP range support is needed. **Revisit** if the extension can be self-hosted.
- **NRT:** not available offline. The card shows the latest complete month of the archive (`index.period.last`), labelled "Latest available month, not live", with the harmonized and NOAA-20 same-month medians. `web/lib/nrt.ts` defines a typed `NrtFetcher` for a future server function; `NRT_ENDPOINT` is null and no key exists in client code.
- **Raw view:** "As recorded" shows, per month, the one platform that is the harmonized source, unscaled (shows the 2012 jump); single-platform views for Terra, Aqua, S-NPP, NOAA-20. No view adds platforms; no combined PK+IN total exists anywhere (D-032).
- **Calendar:** cividis, square-root scale (counts are heavy-tailed); non-colour signals: values in tooltip, live readout and optional in-cell numbers, hatch for no-data, dot for partial months, hatched era band and a rule above 2012. Keyboard: roving tabindex, arrows, Home/End, Ctrl+Home/End.
- **Hotspot CSV for a district:** counted on the district bbox before the polygon filter, so the cap check is conservative.
- **Results finding sentence:** built from t1.json raw/harmonized steps; the night-share clause appears only if the IN Punjab S-NPP 2022–25 mean night share exceeds the 2012–21 maximum (one of the three D-034 conditions; the full pitch logic stays in `blindspot.pitch`).

## D-038 · Review fixes: security, code LOWs, accessibility (31 Oct)
- **Date:** 31 Oct · **Status:** Active · Evidence: `docs/review/*.md` (Resolution sections), `docs/review/axe-after.json`.
- **Dependencies:** maplibre-gl 5.16.0 → 6.16.0 (GHSA-jrc7-96c5-q579; npm audit's fix). MapLibre 6 loads its worker from a separate module, so `maplibre-gl-worker.mjs` is self-hosted in `public/maplibre/` (copied at build) and set with `setWorkerUrl`. postcss forced to 8.5.32 via npm `overrides` (Next 15.5.28 is the latest 15.x and still pins a vulnerable postcss). `npm audit --omit=dev`: 0 vulnerabilities. Rejected: Next 16 major bump (larger retest for a build-time-only advisory).
- **Attribution page:** a dedicated `Marked` instance escapes raw HTML and images and keeps only http(s)/mailto/same-site links. Rejected: DOMPurify (new dependency for a build-time page).
- **serve.mjs:** path check is `root + sep`; invalid Range → 416.
- **t2.json open bins:** `bin_lo_h`/`bin_hi_h` are `null` for open-ended Δ bins; `json.dumps(..., allow_nan=False)` so non-finite values fail loudly.
- **Interval bounds (custom AOI):** a null factor lo/hi makes that month's interval null; it no longer falls back to the point factor.
- **NOAA-20 factor:** fit on 2019–2025, which overlaps the held-out 2022–2025. No pre-registered test uses it. The NOAA-20 era carries `note: "NOAA-20 factor not held-out validated"` in the era docs and on the Methods page.
- **District hotspot CSV (review #1):** decided to **fix, not just add a note**. The tiles get an `adm2_id` column (the exact shape_id from `regions/point_regions.parquet`, left join on lat/lon), and the ADM2 CSV filters with `adm2_id = ?`, so rows match the calendar. Cost: tiles 105 → 108 MB (+3%), appdata +~10 s. Regions (ADM1/rest of box) still use the simplified polygon.
- **Custom-AOI NOAA-20 era (review #2):** **out of scope** for this build. The era starts after S-NPP's last month, and the data runs to 2025-12 with no NOAA-20 era months. Revisit if `snpp_last` moves before the data end.
- **PARTIAL_COVERAGE:** exported as `constants.json.partial_coverage` (from `calibrate.PARTIAL_COVERAGE`); the web no longer hardcodes 0.9.
- **Calendar seam:** the era band splits by the seam month (rows wholly before the switch are MODIS). The seam line is stepped over the 12 months from the switch month. With the January 2012 switch the output is the same.
- **Accessibility:** `--control-border` token (light #6b7884, dark #62788a, ≥3:1); `--nodata` darkened (light #7d8a95, dark #66798a, ≥3.3:1); two-tone calendar focus ring (ink outline + sheet halo); out-of-period cells say ", outside selected period" and hide in-cell values; table wrappers are focusable `role=region`s with labels; skip link + `id="main"`; Escape closes the tooltip and clears the combobox; MapLibre buttons have a themed focus outline; the canvas is named; the combobox list is hidden when it is empty and `aria-expanded` follows it; header cells carry sr-only text; the scope line sits inside `<header>`. Deferred: #14 tap-to-read on phone (optional, info).

## D-039 · T3 explanation tests: orbit drift (O), later burning (T), real decline (D) (written before any T3 number was computed)
- **Date:** 1 Nov 2026 · **Status:** Active. **Pre-registered:** committed alone (before `t3.py` existed and before `make t3` was first run). New analysis, not a change to T1/T2 (rule 6 untouched). Post hoc relative to T2 results (we know the IN Punjab all-days Aqua/S-NPP ratio rose after 2021 and S-NPP counts fell); the rules below are fixed before T3 numbers exist.
- **Common:** regions PK_Punjab, IN_Punjab, rest_of_box (control), each alone; window 15 Oct–30 Nov by local solar date; masked, filtered detections (`calibrate.connect_masked`); per-day scene table from `t2.daily_scene_sql`; days restricted to the platforms' common available days (`calibrate.common_days`). Pre = 2012–2021 (NOAA-20: 2019–2021), post = 2022–2025. PI = `t2.pi_mean_test` (95%, mean of the post years); Theil–Sen = `t2.theil_sen`.
- **What each explanation predicts.** O (Aqua drifts later, VIIRS orbits stable): the Aqua/S-NPP ratio moves as a function of Δ = t_Aqua − t_S-NPP; VIIRS counts and VIIRS night share unchanged. T (burning moves later in the day): VIIRS 13:30 day counts fall, VIIRS night share rises, night counts do not fall; at fixed Δ the Aqua/S-NPP ratio rises. D (less burning): VIIRS day **and** night counts fall; the ratio at fixed Δ is unchanged.
- **A1 NOAA-20/S-NPP.** Σ NOAA-20 / Σ S-NPP (day + night, each platform alone) per year 2019–2025 on common days. **Stable** iff Theil–Sen 95% CI of ln ratio includes 0. Same prediction under O/T/D; if unstable, VIIRS-only conclusions (A2) are marked "sensor-unstable".
- **A2 VIIRS-only.** Per year, S-NPP and NOAA-20 separately: day count, night count, night share, on that platform's available days. **day_fall** / **night_fall**: post mean of ln(count + 1) below the lower bound of the pre PI (S-NPP, pre 2012–21). **night_share_rise**: post mean S-NPP night share > pre max (D-034 rule). NOAA-20 is reported as post vs 2019–21 % change only (3 base years; not used in a rule).
- **A3 close overpass.** Per day Δ from scene times (median local solar hour of each platform's daytime detections, D-033); a day is **usable** iff both have daytime detections and |Δ| < 10 min (1/6 h). Yearly ratio Σ Aqua / Σ S-NPP over usable days and the number of usable days. A post year is evaluable iff ≥ 10 usable days (D-034 analogue). **close_shift:** with ≥ 2 evaluable post years, PI test of their mean ln ratio against 2012–21 → "outside"/"inside"; else "insufficient".
  **Pre-drift curve:** OLS of daily ln(Aqua/S-NPP) on daily Δ over 2012–2021 days with both > 0 (natural day-to-day Δ variation; no post data used). Expected ln ratio of year y = base mean (2012–21 all-days ln ratio) + b·(Δ_y − mean Δ_2012–21), Δ_y = all-days median Δ (as T2). Residual_y = observed all-days ln ratio − expected. **orbit_sufficient** iff the post mean residual is inside the 95% PI from the 2012–21 residuals (`pi_mean_test` on residuals); else "residual remains" with its sign. Extrapolation range: the post Δ_y are compared to the 2.5–97.5% range of daily pre Δ; Δ_y beyond it is reported as "extrapolated beyond the data".
- **A4 factor spread.** Yearly window factor S-NPP/Aqua (all common days, day + night as in T1 hotspots) 2013–2021: mean, sd, CV, sd of ln. **2012 step normal** iff |ln(1 + harmonized_step)| (from `t1.json`) ≤ 2 sd_ln.
- **A5 pre-2012 Terra/Aqua.** Daytime Σ Terra / Σ Aqua per year 2003–2011 on common days; **stable** iff Theil–Sen 95% CI includes 0; CV reported.
- **A6 verdicts (per region).** O: **supported** if orbit_sufficient and close_shift ≠ "outside"; **not supported** if not orbit_sufficient and close_shift = "outside"; else **cannot separate**. D: **supported** if A1 stable, day_fall and night_fall; **not supported** if not day_fall; else **cannot separate**. T: **supported** if night_share_rise, not night_fall, and (residual remains positive or close_shift = "outside" with post > pre); **not supported** if not night_share_rise; else **cannot separate**. Rows list supporting and opposing evidence verbatim from the numbers.
- **A7 reliability flag (per region × calendar year 2003–2025).** `caution` with reason codes, else `yes`: `pre2012_terra_aqua_trend` (year < 2012 and A5 not stable); `splice_step_outside_normal` (year 2012 and A4 step not normal); `aqua_overpass_drift` (year ≥ 2022 and |Δ_y| > 0.5 h, the D-033/D-034 tolerance: the Aqua→S-NPP factor cannot be checked that year); `burning_time_shift` (year ≥ 2022 and T verdict "supported": VIIRS afternoon counts understate burning). Districts inherit the flag of their calibration region (ADM1 = PK Punjab → PK_Punjab, IN Punjab → IN_Punjab, otherwise rest_of_box), written by `make appdata` as `reliability` in each region/district JSON.
- **Pitch:** the "moved later" clause needs T = supported; otherwise the default clause states the correction and that the record flags where it stops being comparable.
- **Rejected:** a quadratic Δ curve (more freedom to absorb the post change); fitting the curve on all years (circular, D-034 b); per-pass times from TLEs (external dependency; not available offline).
- **Results addendum (1 Nov 2026, after the first `make t3`; no rule changed).** Verdicts: PK Punjab O supported, T not supported, D not supported; IN Punjab O cannot separate, T supported, D cannot separate; rest_of_box (control) O cannot separate, T/D not supported (`docs/RESULTS_T3.md`). Caveats recorded by the report, not used to change any verdict: (1) IN night counts are tens per season against tens of thousands by day, so T being supported does not rule out D; the pitch therefore says "some" burning moved later. (2) The pre-drift Δ curve leaves a negative residual in the control, so it is a weak orbit instrument (day-to-day Δ mostly reflects VIIRS swath position). (3) A3 close-overpass is insufficient in every region. Reason text for `burning_time_shift` softened to "may understate it (a real decline is not ruled out)" after seeing (1). `make t2` no longer writes the pitch; `make t3` does. FIRMS DOIs: S-NPP and NOAA-20 now the LP DAAC V002 DOIs (verified on official pages); no FIRMS SP-archive DOI found (`docs/REFERENCES.md`).

## D-040 · Reliability flags in the calendar, T3 on Results, use-case page, NRT function, lint, wording (1 Nov)
- **Date:** 1 Nov · **Status:** Active
- **Flags (D-039 data):** each caution year gets four signals. (1) A triangle icon in a 15th calendar column. (2) A striped year label. (3) A plain-words reason in each cell's accessible name, the tooltip and the readout. (4) A notes list under the calendar. A banner above the calendar appears when the selected period includes a caution year. Plain words per reason code live in `web/lib/reliability.ts`; unknown codes fall back to the data's own text. **Custom AOI rule:** the area takes the union of the flags of every calibration region it overlaps. A region counts as overlapped if any point of a 21×21 grid over the AOI's bbox (inside the circle, for a radius; plus the centre) falls in it. PK is tested before IN, as in D-036; a point in neither belongs to rest_of_box. Rejected: Aqua-detection share (zero detections would drop a region) and the centroid only (wrong across the border).
- **Results:** T3 section with the O/T/D evidence table, VIIRS day vs night by year (log scale, S-NPP and NOAA-20, dash + marker + direct labels) and NOAA-20/S-NPP ratio by year (reference line at 1). Each chart has a data table in `<details>`. All values come from `t3.json`.
- **Use case (`/use-case/`):** Sangrur (IN) and Kasur (PK), November 2025. Value, median, rank among Novembers, the NOAA-20 cross-check and the flag are all computed at build time by `lib/usecase.ts` from the district JSON. Screenshots are written by `e2e/run.mjs` to `public/usecase/`. The Explorer accepts `?area=&from=&to=`. "Sheikhupura" is not in the index under that name, so Kasur was used.
- **NRT:** Cloudflare Pages Function in `web/functions/` (rejected: a Vercel `api/` route, which needs a Next server and breaks the pure static export). Details and test steps in `docs/NRT.md`. The mask cells are exported as `data/nrt/mask_cells.json` by `appdata.nrt_mask_doc`. The card shows the ratio to the median only for complete months.
- **Wording:** the scope line is now "Coverage: Pakistan and northern India. The method should transfer to other regions." (COLD_READ: untested elsewhere). Changed in appdata.py, constants.json, ATTRIBUTION.md, CLAUDE.md rule 9 and PLAN.md. e2e asserts that "Coverage: Coverage" appears on no page.
- **Lint:** ESLint 9 flat config (`next/core-web-vitals` + `next/typescript`), `--max-warnings 0`, run with tsc and vitest in `make web-test`.
- **DuckDB-WASM stays at 1.28.0.** Tried 1.33.1-dev57 (npm `latest`, DuckDB v1.5.4) in Node: `parquet` is neither built in nor installed (`read_parquet` → "exists in the parquet extension"). Self-hosting needs `parquet.duckdb_extension.wasm`, which is published only on extensions.duckdb.org; that host is blocked here (proxy 403), and no npm package ships it. To revisit on a machine with access: download `v1.5.4/wasm_eh/parquet.duckdb_extension.wasm` into `public/duckdb/ext/` and `SET custom_extension_repository`.
- **Other:** long URLs on the Attribution page wrap (they caused 37 px of sideways scroll at 390 px). axe now runs inside `e2e/run.mjs` (6 pages × 2 themes × 2 widths) and writes `docs/review/axe-after.json`.

## D-041 · Deploy prep: Cloudflare Pages Direct Upload, security headers, CSP via hashes (1 Nov)

**What.** Deploy on 14 Nov by `wrangler pages deploy web/out` from a laptop with the data (not Git integration). `web/scripts/gen-headers.mjs` runs after every `next build`: writes `out/_headers` (nosniff, Referrer-Policy, Permissions-Policy, X-Frame-Options DENY, COOP, HSTS, and a header CSP with `frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'`), injects a per-page `<meta>` CSP with sha256 hashes of the inline Next.js scripts plus `'wasm-unsafe-eval'` and `worker-src 'self' blob:`, and fails the build above Cloudflare limits (20,000 files, 25 MiB per file, 100 header rules). `scripts/serve.mjs` applies `_headers` with `HEADERS=1`; `make web-test` and the new `make deploy-rehearsal` run e2e under the headers. `web/wrangler.toml` holds the project name, output dir and the optional `ALLOWED_ORIGIN` var; `FIRMS_MAP_KEY` stays a Pages secret. Team names (`{NAMES}`) are now filled by `story.py` (`TEAM_NAMES`).
**Rejected.** Git-integrated build (data is gitignored and generated from 1.3 GB raw; the build would ship without data). Full CSP in `_headers` (results page has 185 inline scripts; hash list exceeds the 2,000-char line limit). `'unsafe-inline'` for scripts (defeats the CSP). R2/GitHub Releases for tiles (not needed: 4,023 files, largest 21.1 MiB; Releases also lack CORS/Range).
**Evidence.** `gen-headers` output and the e2e summary under headers in `docs/MORNING_SUMMARY.md`; `docs/DEPLOY.md`.

## D-042 · Flagship example, one-sentence lead, critical periods, median excluding flagged years, month-card honesty (1 Nov)
- **Date:** 1 Nov · **Status:** Active · Written before any of the code below. Source: `docs/ARENA_CONCLUSION.md` fixes 2, 3, 4, 6, 7 (fix 4 verified: Sangrur Nov 2025 sits in the Indian Punjab caution list; Kasur Nov 2025 in the Pakistani Punjab list, 2023–2025).
- **Flagship rule (fixed before choosing).** For a named district, the headline month is the November, 2012 to the last full year in the data, with the highest harmonized value among Novembers that are complete (not partial) and whose year is **not** in that district's `reliability.caution_years` (inherited from its calibration region). Ties: the later year. The rule is computed by `story.flagship_month` and `web/lib/usecase.ts` from the district JSON; no year is typed into code. Named districts stay Sangrur (IN) and Kasur (PK) (both large stubble-burning districts already in the index). The 2025 case stays as a second, captioned **contrast** example (it shows the caution banner and the "lowest" wording is dropped from the lead). Rejected: choosing by ratio to the median (the median contains the year itself, so a high month raises the median it is judged against); choosing by lowest value (what the old text did).
- **Month-card ratio display.** The card printed one decimal for ratios under 10, so 0.05 displayed as "0.1×" (the "0.05x" claim was a real display issue, of the opposite kind). New rule: ratios are shown to **2 significant figures** (`fmtRatio`: 0.050, 0.37, 1.7, 12); ratios of 100 or more are rounded to whole numbers. Use-case page and story keep 2 decimals (all ratios there are between 0.1 and 10).
- **One-sentence lead.** SUBMISSION starts, and the video voice-over opens, with one sentence about one place: Pakistani Punjab's record jumps by the raw 2012 step only because the sensor changed; Blind Spot brings it to the harmonized step and flags the years where it stops being comparable. Numbers via `{{t1:...}}`. Voice-over stays ≤ 55 words and the video ≤ 30 s (`tests/test_story.py` already checks both; the shot table is re-timed, not extended).
- **Critical periods (month level only; the data are monthly, no weekly or daily claim).** Per area: (1) baseline = the same baseline years as the existing harmonized median (first data year to the last full year) **minus the area's caution years**. (2) Typical value of month m = median of the complete (not partial) harmonized values of that calendar month over the baseline; a month needs ≥ 5 such years to take part, otherwise it is null. (3) **Critical months** = months whose typical value is ≥ the 75th percentile (linear interpolation, NumPy default) of the participating typical values and is > 0: the top quartile of the year. (4) **Peak** = the month with the highest typical value (earliest on a tie). **Onset** and **end** = first and last month of the run of consecutive critical months (cyclic, December joins January) that contains the peak; critical months outside that run are listed as `other_months`. (5) **This year vs typical**: the latest complete month in the data (`period.last`): its harmonized value, the typical value of that month, the ratio, whether that month is critical, and whether its year is a caution year. Output: `critical` in every district and region JSON (`appdata.critical_periods`), a small text panel on the Explorer (sentence plus a 12-row table, "critical" in words so colour is not the only signal, labelled "month level, not daily"), and comment lines in the calendar CSV. Custom drawn areas have no precomputed block: the panel says so. Rejected: weekly onset/end (no weekly series is shipped; would need new tiles and a new claim); a fixed 15 Oct–30 Nov window (that is the pre-registered test window, not a property of every area); mean instead of median (heavy-tailed).
- **Median excluding flagged years.** New `median_excl_flagged` per area JSON (same shape as `median.harmonized` plus `excluded_years`): the existing monthly median recomputed without the area's caution years. The existing `median.harmonized` is unchanged ("all years"). The month card shows both on separate lines labelled "all years" and "excluding years we flag"; the ratio next to the headline figure **uses the all-years median** (unchanged, and the only one defined for NOAA-20 and drawn areas); the excluding-flagged ratio is shown beside its own median. Critical periods use the excluding-flagged median. Rejected: replacing the old median (silent change of every earlier number); dropping flagged years from the NOAA-20 median (NOAA-20 starts 2019, too few years left).
- **Month card.** The label stays "Latest available month, not live". One added line: the live current month appears when the near-real-time service is switched on at launch. It makes no claim that the service is on.

## D-043 · Critical period and median excluding flagged years for drawn areas (1 Nov)
- **Date:** 1 Nov · **Status:** Active · Written before the code. Closes the open item in CHECKPOINTS F1 ("drawn areas have no critical-period block"). Extends D-042; no definition changes.
- **Rule.** A drawn box or point+radius gets the **same** definitions as a district (D-042), computed in the browser from the custom-area harmonized monthly series (D-036): (1) baseline years = those of the `rest_of_box` region document's harmonized median (as the existing custom median); (2) **caution years of a drawn area = the union of the caution years of the calibration regions it overlaps** (D-040 rule, reused through `overlappedRegions` + `mergeFlags`; nothing new); (3) typical value of month m = median of the complete (not partial) harmonized values over the baseline minus caution years, a month needs >= 5 such years; (4) critical months = typical >= 75th percentile (linear interpolation) of the participating typical values and > 0; peak = highest typical (earliest on a tie); onset/end = ends of the cyclic run containing the peak; others in `other_months`; (5) this-year-vs-typical on the latest complete month. The month card and CSV show both medians ("all years", "excluding years we flag"); the card ratio still uses the all-years median.
- **One implementation.** `web/lib/criticalCalc.ts` (`computeCritical`) holds the logic and is used by the browser for drawn areas only; district/region JSON stays pipeline-computed (rule 7: the pipeline remains the source for precomputed areas).
- **Proof of equality.** `appdata.critical_periods` is the Python reference. `tests/test_critical_crosscheck.py` regenerates `tests/fixtures/critical_crosscheck.json` inputs (harmonized value/partial series + caution years of two real districts, Sangrur and Kasur, plus a synthetic edge case) and the Python output; `web/lib/criticalCalc.test.ts` feeds the same inputs to the TS function and requires equality of months/onset/peak/end/other_months/this_year exactly, and typical values within **0.1** (the one-decimal rounding: Python `round` is half-to-even, JS `Math.round` half-up, so an exact .x5 tie can differ by 0.1) and threshold within 0.1. Months and the run structure are compared exactly. The real-district fixtures are committed (small), since `web/public/data/districts` is gitignored; the Python test re-derives expectations from the fixture inputs so the fixture cannot drift from the reference silently; a second test, skipped when the data are absent, rebuilds the fixture from the live district JSON.
- **Rejected.** A second pipeline-side definition of caution years for drawn areas (would invent a rule); computing the block from the nearest district (wrong for boxes that straddle districts); WASM/Python port (no benefit for 12 numbers).
- **Limits (stated, not hidden).** Drawn areas inherit the caution years of overlapped regions, which is conservative (a box touching a flagged region excludes that region's flagged years everywhere in the box). Month-level only. A drawn area is computed from the simplified Punjab polygons (D-036), so a border-adjacent box can differ slightly in its monthly values; that carries into the typical values.

## D-044 · Interface pass: answer first, phone targets, press feedback, tokens (1 Nov)
- **Date:** 1 Nov · **Status:** Active · Written before the code. Audit and skills used: `docs/review/UI_AUDIT.md`.
- **Planned changes (presentation only; no data-derived text, number or label changes).** (1) Eyebrow "Is this month unusual here?" and a stronger month card (answer first). (2) Step labels in the picker ("1 Choose an area", "2 Choose a period") and an empty state in the stage when no area is loaded. (3) Pressed states on pointer-down for buttons, segmented control, calendar cells and map zoom buttons; tap on a calendar cell sets the readout (closes A11Y #14); touch drawing of the box on the map follows the finger from the touch-down point. (4) Tooltip anchored at its cell with a 100 ms opacity fade. (5) Phone: sticky area-name bar (solid), 44 px targets, full-width actions. (6) Type scale (rem; weights 400/500/600; tight tracking only on large headings) and 4/8 spacing tokens. (7) Dark theme: `--control-border` was undefined under `data-theme=dark`; add it, add a hairline highlight on cards. (8) Motion tokens 100/150/200 ms, transform/opacity only; under `prefers-reduced-motion` no transforms; `prefers-reduced-transparency` and `prefers-contrast: more` branches.
- **Constraints kept.** Caution flags, "latest available month, not live", provisional labels, ODbL attribution, scope line, fail/inconclusive labels stay visible at the same or larger weight; cividis ramp unchanged; axe 0 violations in 6 pages x light/dark x 1440/390; no new dependency, no animation library; bundle size reported before/after.
- **Rejected.** An animation/spring library (bundle, and nothing here is gesture-driven momentum); translucent sticky header (stacked translucency, legibility); rewriting the page layout into tabs (the calendar must stay on one scroll with its caution notes); hiding the month-card footnotes behind a disclosure (honesty text must stay visible).

## D-045 · Track the generated web app data in the private repo (1 Nov)
- **Status:** Active. Supersedes the git policy in D-035 (only small JSON committed, rest rebuilt by `make appdata`).
- **Chosen:** commit `web/public/data` (116 MB, 3,949 files, none over 20 MB) to the private repo `Aiza166/nasa-hackathon`.
- **Rejected:** keeping it gitignored and rebuilding on the deploy computer.
- **Why:** (1) the deploy computer is a Windows PC without `make`, and the rebuild takes about an hour and was untested on Windows; (2) the owner's subscription may end, and the repo must let another person continue with no hidden state; (3) Cloudflare's Git build can now work. Tested on 1 Nov: a clean `git clone`, `npm install` (24 s) and `npm run build` gave a complete site (4,028 files against the 20,000 limit; largest file 21.1 MiB against 25 MiB; 161 MB).
- **Cost:** the repo grows to about 165 MB; each re-run of `make appdata` rewrites binary tiles, so history grows. Do not re-run it casually.
- **Rule kept:** the repo stays private until 14 Nov 09:00 PKT. If it is made public later, the ODbL attribution for the Indian district boundaries travels with the data (`web/public/data/ATTRIBUTION.md`).

## D-046 · Phone answer-first via a collapsible picker, pointer-event drawing, Results/Methods redesign, Windows-safety (1 Nov)
- **Date:** 1 Nov · **Status:** Active · Written before the code. Builds on D-044 (whose "not done" list these four items close). Presentation and tooling only: no number, label or data-derived text changes.
- **1. Phone: answer first without breaking keyboard order.** On widths up to 900 px the area picker (steps 1-3: area, map, period) sits in a collapsible panel. A "Change area" button in the sticky area bar (`aria-expanded`, `aria-controls`) opens it; closed, the panel is `hidden` (not focusable, not in the accessibility tree). DOM order stays: area bar, picker toggle, answer (month card, critical panel), calendar; the picker panel is in the DOM before the answer only when open, because it sits between the toggle and the answer. No CSS `order`. Opening moves focus to the first control in the panel; closing (button or Escape) returns focus to the toggle; a map click or district pick on phone closes it. Height transition is skipped (instant show/hide, so nothing to honour under reduced motion beyond the existing rule). Desktop (over 900 px) is unchanged: the panel is always open and the toggle is hidden. The caution banner, scope line and the "not live" label stay where they were. Rejected: `order`/grid reordering (visual order would differ from tab order, WCAG 2.4.3); moving the map below the answer by duplicating markup (two maps); a bottom sheet with a focus trap (more code, a modal where none is needed).
- **2. Touch drawing.** The MapLibre `touchstart/move/end` handlers are replaced by Pointer Events on the map canvas: `pointerdown` → `setPointerCapture`, corner = the exact point under the pointer (no centre snap), `pointermove` updates the draft, `pointerup` finishes, `pointercancel` and `lostpointercapture` discard. A second active pointer during a draw cancels the draft (pinch is ignored while drawing). `touch-action: none` is applied to the canvas only while draw mode is on (class on the map element), so panning and page scroll work otherwise; MapLibre's drag-pan and touch-zoom are disabled only while drawing. Playwright e2e uses a touch context (hasTouch, isMobile, 390×844) and CDP `Input.dispatchTouchEvent`. Real-device testing is still advised: CDP touch is synthetic.
- **3. Results and Methods.** Results gets an "At a glance" block (one row per test T1/T2/T3 for Pakistani and Indian Punjab; the verdict labels are printed exactly as the JSON has them, with a reason built from the same JSON fields), then the existing tables and charts under headings, a contents list with anchors, keyboard-scrollable table regions (kept), and a 70ch text measure. Methods gets a plain-language summary, numbered sections with anchors (data, harmonization, tests, flags, limitations, AI use), a glossary (hotspot, harmonized, caution year, S-NPP, NOAA-20, median) and the limitations placed directly after the summary's pointer. Rejected: tabs (hides content from print and search), charts redrawn (no data change wanted).
- **4. Windows-safety (not runnable here).** (a) `serve:headers` becomes `node scripts/serve.mjs --headers` (the script still honours `HEADERS=1` so `make web-test` works); new `npm run e2e:full` (`scripts/e2e-full.mjs`) builds if `out/` is missing, picks a free port, serves with headers, runs `e2e/run.mjs`, always stops the server, exits with the test status. (b) `.gitattributes` with `* text=auto`, binary types and `*.sh text eol=lf`. (c) `.nvmrc` = 22 (the clean-clone test); `engines.node` is taken from Next 15.5.28's own `engines` (`^18.18.0 || ^19.8.0 || >= 20.0.0`), not guessed, and the vitest/Playwright toolchain is only tested on 22. (d) POSIX assumptions in `web/scripts` and `web/e2e` are removed with Node APIs. (e) `pwsh` is run only if present. Windows remains unverified until someone runs `npm run e2e:full` there.

**D-046 amendment (2 Nov, verified):** the implementation differs from item 4 above in two places, and the code is the record. (a) `npm run e2e:full` does **not** build or pick a free port: it uses `PORT` (default 4173) and expects `npm run build` to have run first. Run `npm run build` then `npm run e2e:full`. (b) Added `web/.nvmrc` (22), `engines.node >=20`, root `.gitattributes` (LF text, binary for parquet/png/wasm/gz). Verified on Linux only: `npm run build` OK, `npm run e2e:full` 184/184 checks, 0 axe violations, 0 page errors, touch checks included, vitest 33/33, tsc and lint clean. **Not verified on Windows** (no Windows run in this session; `docs/WINDOWS.md` is still untested there).

## D-047 · QA follow-ups: pitch rewrite, explicit median baseline, factor note, two findings closed (2 Nov)
- **Date:** 2 Nov · **Status:** Active · Presentation and wording only; no pipeline number changed.
- **Pitch (PLAN §2).** `pitch.py` now states the season ("October–November") and the harmonized step from `t1.json` (`harmonized_step`: +12.7% and -6.1%), and says "harmonized" instead of "removes it" (the step is reduced, not zero). The word cap moves from 45 to 55 (53 before, 52 now) because the season and the harmonized numbers need the words; the pitch is a summary line and the cap was a convenience, not a rule from PLAN §4. Rejected: dropping the harmonized numbers (the claim "removes it" would stay unsupported), and keeping the cap by cutting the T3 clause (that clause is the finding that matters most for 2022 onward).
- **Median baseline.** The headline ratio (Sangrur 1.74×, Kasur 1.94×) uses the 2003–2025 November median, all years. The ratio excluding flagged years (1.62×, 1.84×) is printed beside it in the submission; the video says "its November median" instead of "the usual November". Rejected: switching the headline to the excluding-flagged median (D-042 fixed the example rule before the data was seen; the card shows both).
- **Methods: size of the Aqua to S-NPP factors.** A paragraph reads the range and median from `results/calibration.json` at build time and cites Schroeder et al. 2014 (375 m pixels detect smaller fires than 1 km pixels). Reason: factors reach 18.2 in Pakistani Punjab in May–June and were unexplained. e2e checks the printed range against the file.
- **First local day of 2003 (QA Q-4): not a defect.** Hypothesis: the 2002 files were not downloaded, so local 1 Jan 2003 loses its UTC 31 Dec evening passes. Test: downloaded `modis_2002_{Pakistan,India}.csv` and mapped every 31 Dec 2002 detection to local solar date: none of the detections in either country's file lands on 1 Jan (India's file has 47 rows on 31 Dec UTC, all local 31 Dec). Both platforms have data on 1 Jan 2003; the only missing days in Jan 2003 are Aqua 30 Jan and Terra 2, 17, 27, 29, 31 Jan. Nothing was changed; the two 2002 files were deleted so `make ingest` does not add a 2002 year to the mask and calibration.
- **One-detection difference (QA Q-6): explained.** `hotspots_filtered` drops exact duplicate rows (same platform, UTC time, lat, lon). There is exactly one in the filtered S-NPP set (2024-05-09 08:26 UTC, 25.68258 N 79.85294 E, in `viirs-snpp_2024_India.csv`). The independent recount did not de-duplicate. The pipeline is right.
- **Still open:** availability is inferred from having at least one detection (D-026), so a real zero-detection day in a small area would count as unavailable; at box and district scale in the study window this is rare and was not measured.

## D-048 · Align the submission docs with the 2026 Project Submission Guide (14 Nov)
- **Date:** 14 Nov · **Status:** Active · Wording and metadata only; no pipeline number, threshold, window or region changed.
- **What.** The 2026 guide (read 14 Nov, notes in `docs/GUIDE_2026_NOTES.md`) replaces the 2025-based assumptions. (1) The submission splits "Demo and project links" into the two 2026 form fields, "Link to Project Demo" and "Link to Final Project", and lists the repository URL under the second. (2) "Use of AI" becomes "Use of Super Intelligence (SI)", the form's name. (3) A "Tools and languages" subsection answers the guide's question on tools, languages, hardware and software, and says in judge-visible text that Claude Code wrote most of the code. (4) "Space agency partner and other data" becomes "Space agency partner data and other references" and lists the open-source software and fonts used. (5) The guide requires SI use in code and data to be acknowledged "in descriptive text and metadata": the README AI section, the `description` and `keywords` of `pyproject.toml` and `web/package.json` now say so. (6) PLAN §0, VIDEO_GUIDE §1 and tasks 08 and 10 carry the confirmed rules (30 s / 7 slides, over the limit not eligible for Global Judging; English; no likeness of anyone under 18; two confirmation boxes; Team Owner's local time for the Universal Event).
- **Rejected.** A per-file "AI-generated" header in every source file: large diff on the deadline day, and the package metadata plus README already meet "descriptive text and metadata". Rewriting the video's last line to the guide's "future" beat: the voice-over is number-sourced and word-capped, and the line choice is the team's (listed as open in `docs/GUIDE_2026_NOTES.md`).
- **How.** Edits were made to the templates (`docs/templates/SUBMISSION.tmpl.md`, `docs/templates/VIDEO_SCRIPT.tmpl.md`) and the same prose was applied to the generated `docs/SUBMISSION.md` and `docs/VIDEO_SCRIPT.md`, because `make story` needs `web/e2e/artifacts/custom_aoi_check.json` (made by `make web-test`, gitignored) and could not run on this machine. No placeholder was added or removed. Re-running `make web-test` then `make story` should leave the generated files unchanged.
- **Also found.** `https://blindspot.pages.dev` already serves another project, so the deploy will need another Pages name (task 08 step 6). The GitHub repo was already public on 14 Nov, which supersedes D-045's "stays private" rule.
