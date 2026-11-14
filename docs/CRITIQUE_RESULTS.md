# Red-team critique of T1/T2 results and the pitch (Skeptic, 31 Oct 2026)

Scope: PLAN §2/§4, DECISIONS D-024..D-033, RESULTS_T1/T2, t1.json/t2.json, t1/t2/calibrate/pitch.py.
Independent queries: read-only DuckDB through `calibrate.connect_masked`. The script is in the scratchpad, not in the repo.

## Numbers checked against t2.json (all match)

| Quantity | t2.json | My query |
|---|---|---|
| PK 2024 matched: Aqua / S-NPP / days | 157 / 3254 / 12 | 157 / 3254 / 12 |
| PK 2025 matched | 41 / 614 / 3 | 41 / 614 / 3 |
| IN 2025 all-days: Aqua / S-NPP, ratio | 2813 / 3670, 0.766 | 2813 / 3670, 0.766 |
| IN 2024 matched | ratio 0.339, 12 days | 769 / 2269 = 0.339, 12 days |

The arithmetic is right. The problems are in what the numbers are taken to mean.

## Issues, strongest first

### 1. FATAL: the pitch's "accounts for +30% and +258%" doesn't compare like with like, and for India it is larger than the rise it is meant to explain
The pitch says the ratio "rose +30% and +86%", which is the 2022–25 **mean**. It then says drift "accounts for +30% and +258% **in 2025**", which is a single year taken from a model. A judge reads that as "drift explains 258% of an 86% rise." The PK pair also looks like a perfect match only by coincidence: +30.3% is the 4-year mean of the all-days ratio, and +30.1% is the modelled effect for 2025 alone. Neither number is a verdict metric.
**Fix:** state one metric for one period, for example "2025 all-days ratio vs 2012–21: PK +X%, IN +Y%; overpass model predicts PK +30%, IN +258%". A better option is to drop percentages from the pitch entirely (see #6).

### 2. MAJOR: the negative control contradicts "consistent with an orbital cause"
`rest_of_box` sees the same Aqua drift. My query gives its all-days Aqua/S-NPP ratio as 0.166 (2021), 0.160 (2023), 0.166 (2024) and **0.172 (2025)**, which is flat. If the ratio rise were orbital, every region at this latitude and in this season should rise. Only IN Punjab rises strongly. PK's all-days ratio peaks at 0.242 in 2023 and is back to 0.182 in 2025.
**Fix:** add rest_of_box (or the full calibration box) to the T2 tables as a pre-declared-style control, labelled post hoc. Reword the conclusion to "orbit drift is necessary for the ratio to move, but its size depends on the region's diurnal burning cycle."

### 3. MAJOR: India's night-share rise points to behaviour, and the orbit cannot produce it
S-NPP's night share in IN Punjab goes from 0.0–0.1% (2012–2022) to 1.4% (2024) and 2.3% (2025). NOAA-20 shows the same, 3.2%. S-NPP's orbit did not change: its scene time stays 13:05–13:15. A shift of burning to later in the day and into the evening, which matches the reported practice of burning after the satellite pass, would do two things at once. It would raise the night share, and it would raise the count from a 14:40 Aqua pass relative to a 13:10 S-NPP pass. That is the same ratio signature as orbit drift. T2b presents night share as consistency evidence, but here it is evidence **against** a purely orbital reading.
**Fix:** say this explicitly in RESULTS_T2 and in the pitch tail. Change "not a change in how the sensors see fire" to "the gap between sensors comes from *when* they look; burning also moved later in the day."

### 4. MAJOR: the "drift effect" coefficient is effectively a post-2022 dummy, so the "back inside range" claim is circular
`Δ_y` is about 0.0–0.25 h for every year up to 2022, then 0.4–1.46 h for 2023–25. An OLS of `ln r_all` on `Δ_y` with n = 14 therefore takes up *any* change after 2022: behaviour, collapsing fire counts in IN (S-NPP daytime detections fell from 73,430 in 2021 to 3,670 in 2025), the S-NPP outage of Nov 2025, and so on. It then calls that change "drift". The adjusted ratio landing "inside the interval" follows by construction. D-033 calls this "descriptive", but pitch.py makes it the test that switches the "consistent with an orbital cause" clause on (`adj_in`).
**Fix:** fit b on 2012–2022 only, or on the within-year day-to-day variation of Δ in 2012–21, and apply it out of sample. If that is not possible, remove the `orbital` branch from pitch.py and keep the adjusted ratio out of the pitch.

### 5. MAJOR: the PK "drift" verdict rests on 15 matched days that shrink with drift, and points the wrong way
The PI rule fires because the matched-days mean falls 37%, driven by 2024 (0.048, 12 days) and 2025 (0.067, 3 days, 41 Aqua fires). The all-days ratio rises. Theil–Sen's CI includes 0, the drift-effect p is 0.11, and the minimum detectable drift is +15%. Matching is also done on the median time of **fire detections**, not on overpass time (D-033). Once Aqua passes at 14:40, a "matched" day is one where S-NPP's fires happened to cluster late, or Aqua caught only the early edge of the swath. That is a selected subset, not a like-for-like comparison.
**Fix:** report PK as "inconclusive: the matched sample collapses after 2023". Require a minimum number of matched days per test year (for example ≥ 10) and treat the test as not evaluable below it. Keep the pre-registered verdict in the table but caveat it in bold.

### 6. MAJOR: the matched-day design does not test "within 30 minutes" for India once drift is large, and a simpler chart says more
My binned query (days with both sensors seeing fire) gives these Aqua/S-NPP ratios for IN by Δ = Aqua − S-NPP scene time:

| Δ bin (h) | 2012–21 | 2022–25 |
|---|---|---|
| (−0.5, 0] | 0.270 | **0.329** |
| (0, 0.5] | 0.248 | 0.267 |
| (0.5, 1.0] | 0.227 | 0.344 |
| (1.0, 1.5] | 0.102 | 0.325 |

The ratio is higher after 2022 even when the passes coincide, and before 2022 a larger Δ went with a *lower* ratio. Overpass time alone does not explain India's rise. For PK the bins are roughly flat at 0.15–0.27 and noisy.
**Fix (a few hours):** replace the T2 percentages in the pitch and slides with two charts. (a) Overpass time by year for Aqua, Terra and S-NPP in both regions. (b) Ratio against Δ, one point per day, coloured by era, with rest_of_box shown beside the two Punjab regions. These carry the honest message: "Aqua now looks 1.5 h later; that changes what it sees in proportion to the local burning clock."

### 7. MAJOR: the 2012 step is read as a sensor change, but the pitch wording is wrong and the step is partly about resolution
"When Aqua is replaced by S-NPP in 2012": Aqua was not replaced. The record is spliced from MODIS (1 km) to VIIRS (375 m), and Aqua kept flying. A judge familiar with MODIS will catch this immediately. "+613%" is also the size of the resolution difference between sensors, not a feature of Punjab.
**Fix:** "when the record switches from MODIS on Aqua to the finer VIIRS on S-NPP in 2012".

### 8. MINOR: T1 is marked "pass" in both regions after T2 found drift, which reads as stronger than it is
The T2 verdict table shows "pass (held-out: not judged)". T1 then rests on a single 2012 step in each region.
**Fix:** relabel as "pass on 2012 step only (n = 1 transition); held-out check void".

### 9. MINOR: the Terra/Aqua "corrected" column in RESULTS_T2 looks like a validation, but Terra's own drift goes uncorrected
Terra moves from 10:55 to 09:35 (earlier, so fewer fires) while Aqua moves later (more fires). That combination alone drives T/A from 0.09 down to 0.008. The "corrected" column moves only slightly (0.008 to 0.029) and still looks like a collapse.
**Fix:** add a footnote that both platforms drift in opposite directions, so T/A cannot separate orbit from behaviour. Grey out the corrected column for 2023+.

### 10. MINOR: in the year tables, the "Δ median (h)" column uses all days while the ratio column uses matched days
A judge will assume that the 2025 PK matched ratio was computed at Δ = 1.46 h. In fact its matched days had |Δ| ≤ 0.5 h.
**Fix:** add a column for median Δ on matched days and rename the existing column to "Δ median, all days".

## Suggested pitch (about 30 s, no percentage for T2)
This is wording only. Under CLAUDE.md rule 7, every number here must come from `pitch.py` reading t1.json/t2.json, including the overpass times from `t2b.overpass`. Do not paste it by hand.
> "In 2012 the fire record switches from MODIS on Aqua to the sharper VIIRS. Read raw, Punjab's fires jump +613% (Pakistan) and +371% (India); harmonized, +13% and −6%. Since 2022 Aqua has drifted from a 1:15 pm to a 2:40 pm pass, so it now sees a different part of the day's burning, while India's farmers have also moved burning later. Blind Spot shows both, corrects the 2012 switch for any district back to 2003, and flags when this month is unusual."

## Response (31 Oct 2026; changes logged as D-034 before recomputing)

| # | Verdict | What changed |
|---|---|---|
| 1 | Accepted, fixed | Pitch has no T2 percentages and no mixed-metric comparison; only the 2012 raw steps are numbers (`pitch.py`). |
| 2 | Accepted, fixed | `rest_of_box` runs through the same T2/T2b code and appears in every T2/T2b table, labelled control, post hoc. Its all-days 2022–25 mean is inside its 2012–21 interval; the pitch's "burns later" clause requires that. |
| 3 | Accepted, fixed | IN night-share rise is one of the three conditions for the "burns later" clause; the clause says behaviour, not orbit. |
| 4 | Accepted, fixed | The overpass-adjusted "back inside" result is labelled circular and drives no verdict and no pitch clause. |
| 5 | Accepted, fixed | D-034 evaluable-year rule (≥ 10 matched days and all-days median Δ within 30 min). PK: only 2022 evaluable → inconclusive. D-033 verdict kept beside it. |
| 6 | Accepted, fixed | Ratio by Δ bin × era per region in t2.json/RESULTS_T2; chart data (overpass by year; one point per day ratio vs Δ) in `data/processed/results/charts_t2.json`. Charts themselves are web work (later checkpoint). |
| 7 | Accepted, fixed | Pitch says "a MODIS-to-VIIRS switch", not "Aqua is replaced". Partial rebuttal: the step is a resolution/sensor effect by design; that is exactly what T1 removes, so it is not presented as a Punjab feature. |
| 8 | Accepted, fixed | T1 label now states its basis ("2012 step only; held-out not judged because T2 is …" or "held-out judged"). Consequence: IN revised T2 is "no drift", so IN held-out is judged and IN T1 is **fail** (held-out fail). Reported, not hidden. |
| 9 | Accepted, fixed | Footnote that Terra and Aqua drift in opposite directions; corrected T/A from 2023 shown in parentheses as not interpretable. |
| 10 | Accepted, fixed | Year tables now have "Δ median, matched days" and "Δ median, all days". |

Not fully resolved: matching still uses detection scene time, not true overpass time (no per-year NASA table, D-033); the IN "no drift" rests on two evaluable years (2022–23) and does not cover 2024–25, when the all-days ratio rose most.
