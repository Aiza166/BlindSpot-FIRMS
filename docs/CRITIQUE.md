# Blind Spot: red-team critique of PLAN.md v1

Skeptic review, 31 Oct 2026. I checked the official challenge page and the Participant FAQ today. 12 issues, strongest first. Severity: FATAL = will disqualify the entry or invalidate the headline. MAJOR = will cost a judging criterion or a key feature. MINOR = cheap to fix, worth fixing.

---

## 1. FATAL: the schedule breaks a published rule

**Problem.** The Participant FAQ (spaceappschallenge.org/resources/participant-faqs) says: *"Teams are not allowed to begin working on the challenges prior to the hackathon."* The Team Formation Guide says participants *"should NOT begin working on their project until the hackathon begins on November 14, 2026 (9:00 a.m. local time)"*. §7 puts ingest, calibration, T1/T2, API, web, deploy and video on D1–D10 (1–10 Nov). That is the whole project, built before the start. §9's mitigation, "dated commits", would be the evidence of the breach. The ❓ in §0 is already answered, and the answer is no.

**Fix.** Rewrite §7 for a window of about 39 hours (Sat 14 Nov 09:00 to Sun 15 Nov 23:59 PKT). Before 14 Nov, do only non-project work: register teammates, get the FIRMS MAP_KEY and Earthdata login, read the FIRMS and MCD14ML user guides, set up generic tooling, and write the method in prose. Ask Chris in writing, today, two questions: (a) is a data download made before 14 Nov allowed? (b) is a written analysis plan allowed? Do not create the repo, push to it, or download data until he answers. Delete the empty `pipeline/` and `web/` folders so they don't suggest earlier work. Issues 7 and 8 assume this 39-hour window.

## 2. FATAL (for the headline): T2's test window is exactly when Aqua's orbit began to drift

**Problem.** The Aqua/S-NPP ratio is only meaningful because both satellites crossed at about 13:30 local time. Aqua stopped its inclination-control manoeuvres around 2021–22, and its crossing time has drifted later since. Terra's has drifted earlier. So the 2022–25 held-out window is the start of an orbit-geometry change. Punjab burning has a strong afternoon peak, so a shift of tens of minutes in Aqua's crossing time moves the ratio mechanically. T2 will very likely report "drift", and that drift will be orbital, not behavioural. A judge who knows the A-Train will say so in the Q&A, and the Validity score is gone.

**Fix.**
- Before 14 Nov, read Aqua's mean local crossing time for each year (NASA ESMO constellation pages) and write it into §0.
- Change T2 to control for overpass time. Option 1: keep only days where Aqua and S-NPP (or NOAA-20) observed the same 0.1° cell within N minutes and at similar scan angles. Option 2: regress the ratio on Δ(overpass time) and test the residual.
- Report "Aqua's drift alone changes the ratio by X%" as a result in its own right. It is a real, operationally useful finding: any constant-ratio calendar that still uses Aqua after 2022 is biased. It is also the honest version of your headline.

## 3. MAJOR: T2 cannot detect the behaviour change the pitch claims

**Problem.** The positive script in §4 says fires "moved out of view" and asks "how much of the decline is real". In Punjab, that means farmers burning after the ~13:30 overpass. That shift removes fires from Aqua **and** S-NPP/NOAA-20 at the same time, because they cross at nearly the same hour. Their ratio barely moves. A stationary ratio is fully consistent with a large hidden decline. The null script ("the calendar can be trusted across the switch") is therefore wrong as worded. T2 tests whether the sensors agree. It does not test whether the record is complete.

**Fix.** Separate the two claims. T2 is about inter-sensor consistency only. Add a cheap timing test, T2b, using data you already have:
- the Terra (morning) to Aqua (afternoon) ratio, corrected for Terra's own drift;
- the VIIRS night (~01:30) to day ratio for Oct–Nov, by year.

A later burning time shows up as a rising night share. Name a geostationary product as future work, and claim nothing beyond it. Reword the null script to: "the two sensors stayed consistent; whether fires moved to unobserved hours is a separate test (T2b)".

## 4. MAJOR: T2 and T1 are statistically ill-posed and not actually pre-registered

**Problem.**
- (a) "2022–25 mean outside the 2012–21 bootstrap 95% interval" compares a 4-year mean with the CI of a 10-year **mean**. That CI shrinks with n and ignores year-to-year variance, so ordinary noise gets flagged as drift. The right yardstick is a prediction interval for the mean of 4 new years.
- (b) "Punjab" is undefined. Pakistan's Punjab and India's Punjab are both in the coverage box and behave differently. Choosing one after seeing the data is exactly what pre-registration is meant to stop.
- (c) T1 and T2 are coupled. If T2 finds drift beyond the interval, the held-out T1 bias of ±15% is likely to fail too. One cause gets scored twice, and the pass/fail outcomes contradict each other.
- (d) The harmonized series is never defined: which sensor feeds which years, and where the splice is. "Harmonized 2012 step" means nothing if Aqua runs to the present with no splice.
- (e) With only 10 calibration years, 4 test years and ±15% bands, nobody has checked whether natural year-to-year variation is already larger than 15%.

**Fix.** Before seeing any data, fix all of the following in writing:
- the AOI as a geoBoundaries ADM1 ID: PK Punjab, IN Punjab, or both reported;
- the splice rule, for example "VIIRS-reference scale; MODIS→VIIRS for 2003–2011, VIIRS from 2012";
- the statistic: Welch t-test or a prediction interval on yearly ratios, plus a Theil–Sen trend with its CI;
- the window: 15 Oct–30 Nov.

Make T1 conditional: "if T2 shows no drift, T1 must pass". State the power: the smallest drift detectable given 2012–21 variance.

## 5. MAJOR: "cell-days at 0.1°" does not match the brief's "number of hotspots", and it saturates at peak season

**Problem.** The brief asks for "a calendar of burning activity showing the **number of hotspots** detected". A 0.1° cell (~11 km × 10 km) in Punjab in early November is active on most days for **both** sensors. The unit saturates exactly when the calendar matters most. That squeezes the ratio towards 1, which by itself biases T2 towards "stationary". It also discards the extra detail VIIRS provides, which the brief explicitly asks you to combine.

**Fix.** Show the calendar in "VIIRS-equivalent hotspots": calibrate counts, using the cell-day model only as a robustness check. Run T1/T2 on 0.05°, 0.1° and 0.25° grids and report the spread. Also report the share of saturated cells (cells with both sensors active) for each month.

## 6. MAJOR: T3 with MCD64A1 is circular and cannot see the target fires

**Problem.** MCD64A1 uses MODIS 1 km active-fire detections to select its training pixels. If MODIS active fires fall, MCD64A1 tends to fall with them, so "counts vs burned area" is not independent. Its 500 m cells are also much coarser than typical Punjab paddy fields (a few hectares), which are often tilled within days. Published evaluations show 500 m burned-area products miss most crop-residue burns there. A falling ratio would not support "fires moved out of view".

**Fix.** Cut T3. It is already a Should, and the 39-hour window cannot carry it. If a check against burned area is wanted, say "Sentinel-2/Landsat burned area would be the independent check" under limitations.

## 7. MAJOR: the critical path in a 39-hour window, and what to cut

**Critical path:**

FIRMS ingest for the box (use the yearly country CSVs, not archive requests, which are queued and can take hours) → cell-day / count tables → calibration + T1/T2 → precomputed calendar JSON for each district → web calendar + median card + CSV → deploy → 30 s video → submission form.

The video and the submission form need about 4 hours. Sleep for an unknown team needs about 10. That leaves about 20–24 build hours.

**What will slip:** NOAA-21 chain, drawn AOI, Urdu, API, T4, design and accessibility passes, cold-reader test.

**Cut now:** T3, T4 (keep only the mask itself), the chat, OpenAQ, Urdu, NOAA-21, district comparison, shareable links, and CP7–CP9 as separate gates.

**Assign by name:** three of the four human roles in §8 are ❓. Before 14 Nov, give one named person the video and the submission, and keep them off the code.

## 8. MAJOR: the API and raw-hotspot CSV will not hold up on a free host during judging

**Problem.**
- A 23-year, multi-platform raw-detection table for 60–80°E × 23–37°N runs to millions of rows. An unbounded `/hotspots.csv` for a large drawn box will time out or run out of memory.
- Render's free tier sleeps and has a cold start of tens of seconds. That is a whole 30 s demo's worth of time.
- Judges open the link days later, when nobody is watching the server.
- Arbitrary lat/lon or box AOIs cannot use the precomputed district fallback, so that feature fails silently if the API is down.

**Fix.** Make the site static-first:
- precomputed JSON for each ADM2 district;
- partitioned Parquet (year × 1° tile) on static hosting, queried in the browser with DuckDB-WASM for custom boxes. This removes the server entirely, except for the NRT proxy.

If you keep the API:
- cap CSV exports (for example 200k rows), and show the user a "narrow your range" message when they hit the cap;
- stream the response;
- host on a platform that does not sleep, or ping it on a schedule;
- write a CP that tests a large-box export.

## 9. MAJOR: the "current month vs median" card compares different data products

**Problem.**
- The card uses FIRMS **NRT** NOAA-20/21. The history uses **standard** data on a harmonized scale.
- NRT CSVs have no `type` field, so §4 step 1 (`type == 0`) cannot be applied. Volcanoes, static sources and offshore flares stay in the current month but are removed from the median. The persistent-hotspot mask (T4) partly covers this only if it is applied to NRT as well.
- NOAA-21 has no calibration against the 2003–2021 median, which is built mainly from Aqua-scaled data.
- The brief's main end-user feature is the one most likely to show a fake anomaly.

**Fix.**
- Compute the current month and the median on the same platform: NOAA-20 for both. NOAA-20 standard data exists from 2018, so the median is short but internally consistent. Show the harmonized median next to it.
- Apply the persistent-hotspot mask to NRT.
- Label the card "near-real-time, provisional".
- Re-check the §3 claim "≤5 days per call" against the current FIRMS API docs.

## 10. MAJOR: "exchange rate drift" will not land with emergency managers in 30 seconds

**Problem.**
- The pitch sentence is a metaphor about method. The judges who wrote this challenge are writing for emergency managers, and they want to know: "is this month unusual for my district?"
- A 30 s video cannot explain an "exchange rate" and then show a product.
- The null outcome ("held within ±Y%") makes a flat headline.
- Issue 2 makes "drift" likely but orbital, so the pitch could promise a behavioural story the data cannot support.

**Fix.** Lead with the user outcome and one number, for example:

> "Satellites changed in 2012 and Aqua's clock drifted after 2022. Uncorrected, Punjab's fires look X% lower than they are. Blind Spot corrects that, for any district, back to 2003."

Show the before/after calendar toggle as the single visual. Keep the T2 method for the project page and the "Best Use of Science" text.

## 11. MINOR: requirements the plan does not fully cover

- **"Download analytics and visualizations."** §5 offers CSVs but no image download. Add PNG/SVG export of the calendar and the median card.
- **"How a current fire compares with previous ones."** The card works at month level. Add one line to the methods page saying that month-level comparison is how the plan interprets "current fire".
- **AI use statement.** The FAQ requires each submission to *"include a description of how [AI] tools were used"*. Given heavy Claude Code use, add this to the CP12 checklist and write it as you go.
- **Team size.** The ≥2 registered members rule applies at the deadline. Confirm that the second member is on the **same** Universal Event team on the team page, not only registered.

## 12. MINOR: fact table hygiene and novelty claims

- **S-NPP date.** §3 marks the end of S-NPP delivery, "2 Nov 2026", as ✅. That date is after the plan's own date (31 Oct). Mark it as "scheduled ⚠️" and don't let the NRT path depend on S-NPP.
- **Theme and demo format.** The 2026 theme and the 30 s / 7-slide limit are still ⚠️. The official guides come out on 13 Nov, so plan the video length to the stricter of the 2025 rules and any new ones.
- **"No competitor repo tests" stationarity.** This may be true of hackathon repos. It is not true of the literature. The shift of Punjab burning to after the overpass has been publicly reported, including by NASA scientists in 2024, and MODIS/VIIRS continuity papers exist. Write "we operationalise and test" rather than "first", cite one source, and don't name competitors (FireLens' R² etc.) in the pitch.
- **Confidence thresholds.** MODIS ≥30 and VIIRS n/h are asymmetric, and smoke changes how often low-confidence flags appear. Run T2 once more with VIIRS l/n/h included, as a robustness check.
