# FIRMS data schema (verified 31 Oct 2026)

What the pipeline expects from FIRMS files, and how sure we are. Markers: ✅ read on an official NASA/FIRMS page · ⚠️ secondary source or inferred · ❓ not verified.

This workspace cannot reach `firms.modaps.eosdis.nasa.gov` directly; the pages below were read through a web-scraping tool on 31 Oct 2026. Re-check every ⚠️/❓ row the first time real files land (`make qc` reports schema drift).

Code: `pipeline/blindspot/schema.py` (column lists, codes), `ingest.py` (normalisation).

## 1. MODIS (Terra + Aqua, C6.1, 1 km)

Source ✅: <https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_MODIS_Firehotspots.html>

| Attribute (as on the page) | Meaning | Status |
|---|---|---|
| Latitude, Longitude | Centre of the 1 km fire pixel | ✅ |
| Brightness | Channel 21/22 brightness temperature, K | ✅ |
| Scan, Track | Actual pixel size (grows toward scan edge) | ✅ |
| Acq_Date, Acq_Time | Acquisition date and time, **UTC** | ✅ |
| Satellite | `A` = Aqua, `T` = Terra | ✅ |
| Confidence | 0–100 %, maps to low / nominal / high classes | ✅ (class boundaries ⚠️, §5) |
| Version | Collection + processing source: `6.1` standard, `6.1NRT`, `6.1RT`, `6.1URT` | ✅ |
| Bright_T31 | Channel 31 brightness temperature, K | ✅ |
| FRP | Fire radiative power, MW | ✅ |
| Type | 0 presumed vegetation fire, 1 active volcano, 2 other static land source, 3 offshore; **only in standard data** | ✅ |
| DayNight | `D` / `N` | ✅ |

Temporal coverage ✅ (same page): Terra from 1 Nov 2000, Aqua from 3 Jul 2002.

## 2. VIIRS (S-NPP, NOAA-20, NOAA-21; 375 m)

Source ✅: <https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_VIIRS_Firehotspots.html>

| Attribute | Meaning | Status |
|---|---|---|
| Latitude, Longitude | Centre of the 375 m pixel | ✅ |
| Bright_ti4 (`Brightness` in web services) | I-4 brightness temperature, K | ✅ |
| Scan, Track | Actual pixel size | ✅ |
| Acq_Date, Acq_Time | UTC | ✅ |
| Satellite | `N` = S-NPP, `N20` = NOAA-20, `N21` = NOAA-21 | ✅ |
| Confidence | `l` / `n` / `h` (low, nominal, high) | ✅ |
| Version | e.g. `2.0NRT`, `2.0RT`, `2.0URT`, `1.0` standard | ✅ |
| Bright_ti5 (`Brightness_2` in web services) | I-5 brightness temperature, K | ✅ |
| FRP | MW | ✅ |
| Type | 0–3 as MODIS (3 includes all detections over water); **only in standard data** | ✅ |
| DayNight | `D` / `N` | ✅ |

Temporal coverage ✅ (layer page and FIRMS FAQ <https://www.earthdata.nasa.gov/data/tools/firms/faq>): S-NPP from 20 Jan 2012, NOAA-20 from 1 Jan 2020, NOAA-21 from 17 Jan 2024. **Conflict:** D-015 says NOAA-20 standard data start in April 2018 (FIRMS archive page). The FAQ says 1 Jan 2020. The downloader requests NOAA-20 from 2018 (a missing year is recorded as `not_found`, not an error); check which years actually arrive before fitting the NOAA-20→S-NPP factor.

S-NPP: delivery ceases 2 Nov 2026 ✅ (FIRMS banner, both layer pages).

## 3. Exact CSV header and the yearly country files

| Fact | Status | Source |
|---|---|---|
| Country Yearly Summary page exists, "based on Standard Processing (SP)", products **MODIS, VIIRS NOAA-20, VIIRS S-NPP** (ids `modis`, `viirs-jpss1`, `viirs-snpp`); no NOAA-21 | ✅ | <https://firms.modaps.eosdis.nasa.gov/country/> (page HTML) |
| File URL pattern `https://firms.modaps.eosdis.nasa.gov/data/country/{product}/{year}/{product}_{year}_{Country}.csv` | ⚠️ secondary only | Third-party example `…/data/country/viirs-snpp/2025/viirs-snpp_2025_Netherlands.csv` (opendataindex.nl, retrieved Oct 2026); the FIRMS page builds links in JavaScript, which we could not read |
| Zip bundle `…/data/country/zips/{product}_{year}_all_countries.zip` holding `{product}_{year}_{Country}.csv` | ⚠️ secondary | GitHub issue mapme-initiative/mapme.biodiversity#264 (May 2024) |
| Country spelling in file names (e.g. `Pakistan`, `India`) | ❓ | assumed from the examples above |
| Header is lower-case snake_case: MODIS `latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type`; VIIRS `latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight,type` | ⚠️ | Attribute names ✅ (§1–2); lower-case form and the `instrument` column as FIRMS API/CSV output shows them (Firecrawl FIRMS provider contract, which also lists `country_id` as a possible extra column); exact order ❓ |
| `acq_time` is HHMM and may lose leading zeros (`45` = 00:45) | ⚠️ | common in FIRMS CSVs; ingest pads to 4 digits |

How the code copes: the URL pattern is a setting (`--url-template` or `BLINDSPOT_FIRMS_COUNTRY_URL_TEMPLATE`); if no file arrives, the CLI exits 2 and says how to copy the right link from the country page. Header matching is case-insensitive and order-free; only the columns in `schema.REQUIRED_COLUMNS` must be present; `type` and `instrument` are optional; MODIS vs VIIRS is decided from `instrument`, then the brightness columns, then the file name. Extra or missing columns are reported by `make qc` (schema drift), never silently dropped.

## 4. Area API (near-real-time card)

Source ✅: <https://firms.modaps.eosdis.nasa.gov/api/area/>

- `/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]` → most recent data, today back to today − (DAY_RANGE − 1). ✅
- `/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]/[DATE]` → `[DATE] .. [DATE + DAY_RANGE − 1]`. ✅
- `SOURCE`: `LANDSAT_NRT` (US/Canada), `MODIS_NRT`, `MODIS_SP`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA20_SP`, `VIIRS_NOAA21_NRT`, `VIIRS_NOAA21_SP`, `VIIRS_SNPP_NRT`, `VIIRS_SNPP_SP`. ✅
- `AREA_COORDINATES`: `west,south,east,north` or `world`. ✅ Our box: `60,23,80,37`.
- `DAY_RANGE`: 1..5. ✅
- `DATE`: `YYYY-MM-DD`, optional. ✅
- NRT "RT and URT data are removed when corresponding NRT detections are processed or RT/URT is older than 6 hours". ✅
- Transaction limit: 5000 transactions per 10 minutes per key, each day of `DAY_RANGE` counting as one. ⚠️ (Firecrawl FIRMS provider contract; the FIRMS page only links to a "Check status" tool). The client budgets 4000 per 10 minutes and waits ≥1 s between calls.
- The API returns HTTP 200 with a plain-text message for errors such as a bad key ❓; the client treats any response whose first line is not a CSV header as an error and redacts the key from the message.
- NRT files have no `type` column ✅ (layer pages: Type only in standard data). VIIRS NRT confidence may be spelled out (`low`/`nominal`/`high`) in the active-fire text files ⚠️; ingest accepts both forms.

## 5. Confidence classes

- MODIS: FIRMS FAQ ✅ says the 0–100 value "can be used to assign one of the three fire classes" but does not print the boundaries. The boundaries used — low < 30, nominal 30–79, high ≥ 80 — are the MODIS C6/C6.1 Active Fire User's Guide values ⚠️ (not re-read here). The filter itself (≥ 30) is fixed by PLAN.md §4.
- VIIRS: l / n / h ✅. Filter n/h, robustness l/n/h (PLAN.md §4).

## 6. Archive download Readme

Source ✅: <https://firms.modaps.eosdis.nasa.gov/download/Readme.txt>

- Emailed archive zips use `fire_archive_*` (standard) and `fire_nrt_*` (NRT) CSVs; NRT is replaced by standard data after about 3 months.
- Known MODIS gaps: end June–start July 2001, scattered 2002, from mid-August 2007, part of 21 Apr and all of 22 Apr 2009. `make qc` lists zero-row days so these can be checked.
- Coordinates are WGS84 lat/lon.

## 7. Normalised table (pipeline output)

`data/processed/hotspots/year=YYYY/platform=NAME/*.parquet` (year = UTC year of `acq_date`):

`platform` (Terra/Aqua/SNPP/NOAA20/NOAA21), `instrument` (MODIS/VIIRS), `lat`, `lon`, `acq_datetime_utc` (timestamptz), `local_solar_datetime` (UTC + lon/15 h, naive), `acq_date`, `daynight`, `confidence_raw`, `confidence_class`, `frp`, `scan`, `track`, `type`, `version`, `processing` (standard/NRT/RT/URT), `source_file`, `source_row`, flags `passes_standard`, `passes_type`, `passes_conf`, `passes_conf_robust`, `in_box`. DuckDB views (`ingest.connect`): `hotspots` (+ `is_duplicate`), `hotspots_filtered`, `hotspots_filtered_nrt`; after `mask.apply_mask`: `hotspots_masked_flags`, `hotspots_masked`.

## 8. geoBoundaries ADM1 / ADM2 (PAK, IND)

Source ✅: geoBoundaries gbOpen, official index <https://raw.githubusercontent.com/wmgeolab/geoBoundaries/main/releaseData/geoBoundariesOpen-meta.csv> (read 31 Oct 2026; sha256 of the copy read `d6f81bc9d3239f63fc36a62c6e3774ae892cedd5c653b8873fe1148311929eea`). Geometry: `https://github.com/wmgeolab/geoBoundaries/raw/4004e96/releaseData/gbOpen/{ISO}/{ADM}/geoBoundaries-{ISO}-{ADM}.geojson` (commit `4004e96`, the one the index's `staticDownloadLink` pins). Project-level licence (repo `LICENSE`/README ✅): geoBoundaries code and derivative works CC BY 4.0, and "the only requirement for use is acknowledgement". Each boundary set carries its own source licence:

| Set | boundaryID | Year | Source (index) | Licence (index) | Units | Status |
|---|---|---|---|---|---|---|
| PAK ADM1 | PAK-ADM1-70912109 | 2019 | geoBoundaries, Wikipedia | Public Domain | 7 | ✅ index |
| PAK ADM2 | PAK-ADM2-60131773 | 2019 | geoBoundaries, Wikipedia | Public Domain | 126 | ✅ index |
| IND ADM1 | IND-ADM1-1811400 | 2011 | DataMeet India community, Election Commission of India | CC BY 2.5 IN (attribution) | 36 | ✅ index |
| IND ADM2 | IND-ADM2-76128533 | 2021 | Pathways Data Pvt. Ltd., lgdirectory.gov.in | ODbL 1.0 (attribution + share-alike for the database) | 736 | ✅ index |

Attribution needed in the app: "Boundaries: geoBoundaries (Runfola et al. 2020), CC BY 4.0; India states © DataMeet (CC BY 2.5 IN); India districts © Pathways Data (ODbL 1.0)". ODbL share-alike applies if we redistribute a derived boundary database (e.g. district polygons in the web app).

- The index also has a row `IND-ADM0-90661403` typed `ADM1`; the downloader matches on the `boundaryID` prefix and skips it.
- **Files are Git LFS objects.** raw.githubusercontent.com serves only the LFS pointer; the real file comes from media.githubusercontent.com. ❓ **Not downloaded in the analyst workspace** (its proxy refuses the LFS hosts, D-030). `make boundaries` refuses an LFS pointer and records `status: lfs_pointer` in `data/raw/boundaries/manifest.json`.
- PK Punjab shapeID: `70912109B12169979015230` (PAK ADM1, shapeName "Punjab"); IN Punjab shapeID: `1811400B91946361694107` (IND ADM1, shapeName "Punjab"). ✅ from `make regions`, 31 Oct. Geometry fetched from media.githubusercontent.com at pinned commit 4004e96 (Git LFS).
- Border overlap: 9,539 of 4,774,182 points fall inside both Punjab polygons (PAK and IND files come from different sources). They count in both regions' separate tests (D-032).
- Fields used: `shapeName`, `shapeID` (feature properties) ✅ confirmed on the real files.
- Derived table `data/processed/regions/point_regions.parquet`: `lat`, `lon` (exactly as in the hotspot table), `level` (`ADM1`/`ADM2`/`CALIB`), `shape_iso`, `shape_id`; CALIB ids `PK_Punjab`, `IN_Punjab`, `rest_of_box`.

## 9. Citations (FIRMS)

Checked 1 Nov 2026 (D-039; details in `docs/REFERENCES.md`):
- MODIS C6.1 MCD14ML: doi:10.5067/FIRMS/MODIS/MCD14ML. The FIRMS citation string; listed as a cited DOI in NASA's citation records (https://access.earthdata.nasa.gov/citations/CIT3804242140-ESDIS). No product landing page with this DOI was found, and doi.org could not be reached from the analyst workspace.
- VIIRS S-NPP 375 m standard: doi:10.5067/VIIRS/VNP14IMG.002 (VIIRS/NPP Active Fires 6-Min L2 Swath 375m V002, LP DAAC, https://www.earthdata.nasa.gov/data/catalog/lpcloud-vnp14img-002).
- VIIRS NOAA-20 375 m standard: doi:10.5067/VIIRS/VJ114IMG.002 (VIIRS/JPSS1 Active Fires 6-Min L2 Swath 375m V002, Giglio 2024, LP DAAC, https://www.earthdata.nasa.gov/data/catalog/lpcloud-vj114img-002).
- Not verified: a separate FIRMS-issued DOI for the FIRMS standard (SP) archive, and that the FIRMS SP files are built from collection V002 (FIRMS pages checked do not state it). The earlier `…_NRT.002` DOIs are the near-real-time products and apply only to NRT data.
