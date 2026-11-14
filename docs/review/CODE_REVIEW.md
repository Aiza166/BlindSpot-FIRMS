# Code review: Blind Spot

Static read of pipeline/blindspot/*.py and web/lib, web/components and web/app, done by a feature-dev code-reviewer agent and saved by the lead. No HIGH or MEDIUM findings.

**Checked and found correct:** the custom-AOI splice matches the pipeline; the CSV cap is checked before the query and also enforced by LIMIT; no platform sums; the test window is 15 Oct to 30 Nov; calibration uses 2012–2021 only; no combined PK+IN total; all SQL is parameterised; there is no key in web/.

## LOW findings

1. **District hotspot CSV uses the simplified polygon** (Explorer.tsx:202-211; appdata.py:374-387). Row totals can differ from the calendar counts near the district edge (~1 km). Fix: put the exact `shape_id` in the tiles and filter by it, or say in the CSV header that the edge is approximate.
2. **Custom-AOI series have no NOAA-20-scaled era** (series.ts:127; appdata.py:559-572). Not triggered by data up to 2026-10. Fix: export the NOAA20→SNPP factors, or state that this era is out of scope.
3. **Null lo/hi bounds fall back to the point factor** (series.ts:118-119). This understates uncertainty. Fix: treat null as undefined.
4. **The NOAA-20 factor is fit on 2019–2025, which includes the held-out 2022–2025** (calibrate.py:33, 439-446). PLAN §4 states this, and no held-out test uses NOAA-20. Fix: add a DECISIONS note and label the factor "not held-out validated".
5. **t2.json contains `Infinity`**, which is invalid JSON (t2.py:222-238, 513). Fix: write null for open-ended bins.

## Notes
- series.ts:8 hardcodes `PARTIAL_COVERAGE = 0.9`. Export it in constants.json instead (rule 7).
- Calendar.tsx:92 splits the eras by year, which is correct only while the sensor switch falls in January.

## Resolution (31 Oct, D-038)
- **#1 fixed:** the tiles carry the exact `adm2_id` from `point_regions.parquet`, and the ADM2 hotspot CSV filters on it (tiles +3%).
- **#2 deferred, out of scope:** no NOAA-20-scaled months exist in the data (it ends 2025-12). Logged in D-038.
- **#3 fixed:** a null lo or hi makes the month's interval null.
- **#4 fixed:** D-038 note. The NOAA-20 era has `note: "NOAA-20 factor not held-out validated"`, and the Methods page shows it.
- **#5 fixed:** null for open bins, plus `allow_nan=False`. `make t2` and `make appdata` were regenerated, and t2.json has 0 `Infinity`. Tests: `test_delta_bins_open_ends_are_null_and_json_strict`, `test_report_and_pitch_accept_null_bin_edges`.
- **Notes fixed:** `constants.json.partial_coverage` (`test_constants_export_partial_coverage_from_calibrate`). The calendar era split now uses the seam month.
