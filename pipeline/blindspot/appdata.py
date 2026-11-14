"""Static data for the web app (PLAN.md §6; D-009, D-010, D-031, D-035).

Reads existing pipeline outputs only; computes no new science except per-calendar-month
medians of series that already exist. Writes to web/public/data/:

* districts/{shape_id}.json  every ADM2 district in the coverage box
* regions/{pk_punjab,in_punjab,rest_of_box}.json
* index.json (district list + licences), districts.geojson (simplified boundaries)
* tiles/year=YYYY/tile_{lat}_{lon}.parquet + tiles/manifest.json (masked, filtered hotspots)
* constants.json, results/*.json (incl. calibration.json, D-036), ATTRIBUTION.md

Platforms are never added together (CLAUDE.md rule 1): each raw platform is its own array.

    python -m blindspot.appdata --processed data/processed --boundaries data/raw/boundaries \
        --out web/public/data
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from blindspot import provenance
from blindspot.calibrate import PARTIAL_COVERAGE, SNPP_FIRST_MONTH, SNPP_LAST_MONTH
from blindspot.ingest import COVERAGE_BOX
from blindspot.regions import IN_PUNJAB, PK_PUNJAB, REST

SCHEMA_VERSION = 1
CSV_ROW_CAP = 200_000  # D-009
TILE_DEG = 1
PLATFORMS = ("Terra", "Aqua", "SNPP", "NOAA20")
HARMONIZED_UNIT = "S-NPP-equivalent hotspots"
RAW_UNIT = "hotspots (masked, filtered, one platform each; never summed)"
# D-010: the current-month card compares NOAA-20 with a NOAA-20 standard median from 2019.
NOAA20_BASELINE_FIRST = 2019
PLATFORM_FIRST_YEAR = {"Terra": 2003, "Aqua": 2003, "SNPP": 2012, "NOAA20": NOAA20_BASELINE_FIRST}
REGION_FILES = {PK_PUNJAB: "pk_punjab", IN_PUNJAB: "in_punjab", REST: "rest_of_box"}
SIMPLIFY_TOL_DEG = 0.01
COORD_DECIMALS = 3
# Punjab outlines for client-side region assignment (D-036): finer than the map outlines,
# because detections near the PK/IN border get different factors.
CALIB_POLY_TOL_DEG = 0.0005
CALIB_POLY_DECIMALS = 5
TILE_COMPRESSION = "zstd"
REQUIRED_KEYS = (
    "schema_version",
    "id",
    "level",
    "name",
    "country",
    "adm1",
    "bbox",
    "period",
    "units",
    "eras",
    "harmonized",
    "raw",
    "median",
    "provenance",
)

FIRMS_CITATIONS = (
    {
        "product": "MCD14ML",
        "text": "MODIS Collection 6.1 Hotspot / Active Fire Detections MCD14ML distributed "
        "from NASA FIRMS. Available on-line https://earthdata.nasa.gov/firms.",
        "doi": "10.5067/FIRMS/MODIS/MCD14ML",
    },
    {
        "product": "VNP14IMG",
        "text": "VIIRS/NPP Active Fires 6-Min L2 Swath 375m V002 (VNP14IMG; FIRMS standard "
        "archive, distributed from NASA FIRMS, https://earthdata.nasa.gov/firms). DOI from the "
        "LP DAAC record https://www.earthdata.nasa.gov/data/catalog/lpcloud-vnp14img-002.",
        "doi": "10.5067/VIIRS/VNP14IMG.002",
    },
    {
        "product": "VJ114IMG",
        "text": "VIIRS/JPSS1 Active Fires 6-Min L2 Swath 375m V002 (VJ114IMG; FIRMS standard "
        "archive, distributed from NASA FIRMS, https://earthdata.nasa.gov/firms). DOI from the "
        "LP DAAC record https://www.earthdata.nasa.gov/data/catalog/lpcloud-vj114img-002.",
        "doi": "10.5067/VIIRS/VJ114IMG.002",
    },
)


def licenses() -> list[dict]:
    """Licences of redistributed data (D-031)."""
    gb = "geoBoundaries gbOpen (Runfola et al. 2020, https://www.geoboundaries.org)"
    return [
        {
            "dataset": "geoBoundaries PAK ADM1",
            "licence": "Public Domain",
            "source": gb,
            "applies_to": ["regions/pk_punjab.json (bbox)"],
        },
        {
            "dataset": "geoBoundaries PAK ADM2",
            "licence": "Public Domain",
            "source": gb,
            "applies_to": ["districts.geojson (PAK features)", "districts/ (PAK)"],
        },
        {
            "dataset": "geoBoundaries IND ADM1",
            "licence": "CC BY 2.5 IN (attribution; source DataMeet India community, "
            "Election Commission of India)",
            "source": gb,
            "applies_to": ["regions/in_punjab.json (bbox)", "index.json adm1 names (IND)"],
        },
        {
            "dataset": "geoBoundaries IND ADM2",
            "licence": "ODbL 1.0 (Open Data Commons Open Database License 1.0; source "
            "Pathways Data Pvt. Ltd., lgdirectory.gov.in)",
            "source": gb,
            "applies_to": ["districts.geojson (IND features)", "districts/ (IND)"],
            "note": "The simplified IND ADM2 boundaries derived here are distributed under "
            "ODbL 1.0 with attribution (share-alike), per D-031.",
        },
        {
            "dataset": "NASA FIRMS active fire data",
            "licence": "NASA open data; cite as below",
            "source": "https://earthdata.nasa.gov/firms",
            "citations": list(FIRMS_CITATIONS),
            "applies_to": ["tiles/", "districts/", "regions/", "results/"],
        },
    ]


def attribution_markdown() -> str:
    lines = [
        "# Data attribution and licences",
        "",
        "Generated by `make appdata` (pipeline/blindspot/appdata.py). Coverage: Pakistan and "
        "northern India. The method should transfer to other regions.",
        "",
        "## Boundaries: geoBoundaries gbOpen",
        "",
        "Runfola, D. et al. (2020) geoBoundaries: A global database of political "
        "administrative boundaries. PLoS ONE 15(4): e0231866. https://www.geoboundaries.org",
        "",
        "| Set | Licence | Source |",
        "|---|---|---|",
        "| PAK ADM1 | Public Domain | geoBoundaries, Wikipedia |",
        "| PAK ADM2 | Public Domain | geoBoundaries, Wikipedia |",
        "| IND ADM1 | CC BY 2.5 IN | DataMeet India community, Election Commission of India |",
        "| IND ADM2 | ODbL 1.0 | Pathways Data Pvt. Ltd., lgdirectory.gov.in |",
        "",
        "**IND ADM2 (ODbL 1.0):** `districts.geojson` contains simplified IND ADM2 boundaries "
        "derived from geoBoundaries IND ADM2. This derived database is made available under "
        "the Open Data Commons Open Database License 1.0 "
        "(https://opendatacommons.org/licenses/odbl/1-0/), with attribution to geoBoundaries "
        "and Pathways Data Pvt. Ltd. (D-031).",
        "",
        "## Fire detections: NASA FIRMS",
        "",
        "We acknowledge the use of data and imagery from LANCE FIRMS operated by NASA's "
        "Earth Science Data and Information System (ESDIS).",
        "",
    ]
    for c in FIRMS_CITATIONS:
        lines.append(f"- {c['text']} doi:{c['doi']}")
    lines += [
        "",
        "Hotspot tiles are masked (persistent-hotspot mask, D-024) and filtered (PLAN.md §4). "
        "Near-real-time data, where shown, is provisional.",
        "",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ series documents


def ym(y: int, m: int) -> str:
    return f"{int(y):04d}-{int(m):02d}"


def month_range(first: tuple[int, int], last: tuple[int, int]) -> list[tuple[int, int]]:
    out, (y, m) = [], first
    while (y, m) <= last:
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def last_complete_month(harm: pd.DataFrame) -> tuple[int, int]:
    """Last month of the harmonized grid, with trailing partial (<90% days) months dropped."""
    g = harm.groupby(["year", "month"])["partial"].any().sort_index()
    for (y, m), part in reversed(list(g.items())):
        if not part:
            return int(y), int(m)
    raise ValueError("no complete month")


def _r(x, nd: int = 1):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return round(float(x), nd)


def monthly_median(df: pd.DataFrame, years: tuple[int, int], col: str = "value") -> dict:
    """Median per calendar month over baseline years (inclusive), complete months only."""
    d = df[(df.year >= years[0]) & (df.year <= years[1]) & ~df.partial.astype(bool)]
    d = d[d[col].notna()]
    vals, ns = [], []
    for m in range(1, 13):
        s = d.loc[d.month == m, col]
        vals.append(_r(s.median()) if len(s) else None)
        ns.append(int(len(s)))
    return {
        "baseline_years": [int(years[0]), int(years[1])],
        "rule": "median over baseline years of complete months (>=90% days available)",
        "values": vals,
        "n_years": ns,
    }


MIN_YEARS_CRITICAL = 5  # D-042: a calendar month needs this many unflagged complete years


def _run_around(months: set[int], peak: int) -> list[int]:
    """Cyclic run of consecutive calendar months (1-12) inside `months` that contains `peak`."""
    start = peak
    while (start - 2) % 12 + 1 in months and (start - 2) % 12 + 1 != peak:
        start = (start - 2) % 12 + 1
    run, cur = [start], start
    while cur % 12 + 1 in months and cur % 12 + 1 != start:
        cur = cur % 12 + 1
        run.append(cur)
    return run


def critical_periods(
    harm: pd.DataFrame,
    caution_years: list[int],
    last_month: tuple[int, int],
    first_year: int = 2003,
) -> tuple[dict, dict]:
    """(median_excl_flagged, critical) at month level (D-042)."""
    end_year = _full_year_end(last_month)
    hm = _upto(harm, last_month)
    excl = sorted(int(y) for y in caution_years if first_year <= int(y) <= end_year)
    med = monthly_median(hm[~hm.year.isin(excl)], (first_year, end_year))
    med["excluded_years"] = excl
    med["rule"] = "median over baseline years of complete months, caution years left out"
    typ = {
        m + 1: v
        for m, (v, n) in enumerate(zip(med["values"], med["n_years"], strict=True))
        if v is not None and n >= MIN_YEARS_CRITICAL
    }
    crit: dict = {
        "resolution": "month",
        "baseline_years": med["baseline_years"],
        "excluded_years": excl,
        "min_years": MIN_YEARS_CRITICAL,
        "rule": "critical months = typical value at or above the 75th percentile of the "
        "twelve typical monthly values (excluding caution years), above zero",
        "threshold": None,
        "months": [],
        "onset": None,
        "peak": None,
        "end": None,
        "other_months": [],
        "this_year": None,
    }
    if typ:
        q75 = float(np.percentile(list(typ.values()), 75))
        crit["threshold"] = _r(q75)
        cm = {m for m, v in typ.items() if v >= q75 and v > 0}
        if cm:
            peak = min(cm, key=lambda m: (-typ[m], m))
            run = _run_around(cm, peak)
            crit.update(
                months=sorted(cm),
                onset=run[0],
                peak=peak,
                end=run[-1],
                other_months=sorted(cm - set(run)),
            )
    ly, lm = last_month
    row = hm[(hm.year == ly) & (hm.month == lm)]
    if len(row) and not bool(row.partial.iloc[0]) and pd.notna(row.value.iloc[0]):
        v, t = float(row.value.iloc[0]), med["values"][lm - 1]
        crit["this_year"] = {
            "month": ym(ly, lm),
            "value": _r(v),
            "typical": t,
            "ratio": _r(v / t, 3) if t else None,
            "in_critical": lm in crit["months"],
            "year_flagged": ly in {int(y) for y in caution_years},
        }
    return med, crit


def eras(last: tuple[int, int]) -> list[dict]:
    y, m = SNPP_FIRST_MONTH
    pre = (y - 1, 12) if m == 1 else (y, m - 1)
    out = [
        {"start": "2003-01", "end": ym(*pre), "label": "MODIS-scaled", "source": "Aqua"},
        {
            "start": ym(*SNPP_FIRST_MONTH),
            "end": ym(*SNPP_LAST_MONTH),
            "label": "S-NPP",
            "source": "SNPP",
        },
    ]
    ny, nm = SNPP_LAST_MONTH
    nxt = (ny + 1, 1) if nm == 12 else (ny, nm + 1)
    out.append(
        {
            "start": ym(*nxt),
            "end": None,
            "label": "NOAA-20-scaled",
            "source": "NOAA20",
            # fit on 2019-2025, which overlaps the held-out 2022-2025 (D-038)
            "note": "NOAA-20 factor not held-out validated",
        }
    )
    for e in out:
        e["in_series"] = e["start"] <= ym(*last)
    return out


def _full_year_end(last: tuple[int, int]) -> int:
    return last[0] if last[1] == 12 else last[0] - 1


def _upto(df: pd.DataFrame, last: tuple[int, int]) -> pd.DataFrame:
    return df[(df.year * 100 + df.month) <= last[0] * 100 + last[1]]


def area_doc(
    meta: dict,
    harm: pd.DataFrame,
    raw: pd.DataFrame,
    last_month: tuple[int, int],
    provenance: dict,
    first_month: tuple[int, int] = (2003, 1),
    caution_years: list[int] | None = None,
) -> dict:
    """One district/region document. harm/raw are rows of one shape only."""
    months = month_range(first_month, last_month)
    hidx = harm.set_index(["year", "month"])
    end_year = _full_year_end(last_month)

    def hcol(c, nd=1):
        return [_r(hidx[c].get((y, m))) if (y, m) in hidx.index else None for y, m in months]

    harmonized = {
        "value": hcol("value"),
        "lo": hcol("value_lo"),
        "hi": hcol("value_hi"),
        "source": [
            str(hidx["source_platform"].get((y, m))) if (y, m) in hidx.index else None
            for y, m in months
        ],
        "partial": [
            bool(hidx["partial"].get((y, m))) if (y, m) in hidx.index else None for y, m in months
        ],
    }
    hm = _upto(harm, last_month)
    median = {"harmonized": monthly_median(hm, (first_month[0], end_year))}
    raw_out = {}
    for p in PLATFORMS:
        rp = raw[raw.platform == p]
        ridx = rp.set_index(["year", "month"])
        raw_out[p] = {
            "n": [int(ridx["n"].get((y, m))) if (y, m) in ridx.index else None for y, m in months],
            "partial": [
                bool(ridx["partial"].get((y, m))) if (y, m) in ridx.index else None
                for y, m in months
            ],
        }
        rpm = _upto(rp, last_month)
        median[p] = monthly_median(
            rpm.rename(columns={"n": "value"}), (PLATFORM_FIRST_YEAR[p], end_year)
        )
    med_ex, critical = critical_periods(harm, caution_years or [], last_month, first_month[0])
    return {
        "schema_version": SCHEMA_VERSION,
        **meta,
        "period": {"first": ym(*months[0]), "last": ym(*months[-1]), "n_months": len(months)},
        "units": {"harmonized": HARMONIZED_UNIT, "raw": RAW_UNIT, "time": "local solar month"},
        "eras": eras(last_month),
        "harmonized": harmonized,
        "raw": raw_out,
        "median": median,
        "median_excl_flagged": med_ex,
        "critical": critical,
        "provenance": provenance,
    }


def calib_region_of(meta: dict, regions_meta: dict) -> str:
    """Calibration region a district inherits its reliability flag from (D-039)."""
    a1 = (meta.get("adm1") or {}).get("id")
    for rid in (PK_PUNJAB, IN_PUNJAB):
        if a1 is not None and a1 == (regions_meta[rid].get("adm1") or {}).get("id"):
            return rid
    return REST


def reliability_doc(t3: dict, region: str, inherited: bool) -> dict:
    """Per-year 'harmonization reliable' flag from t3.json (D-039)."""
    rel = t3["t3"][region]["reliability"]
    caution = {y: v["reasons"] for y, v in rel.items() if v["harmonization_reliable"] == "caution"}
    used = {c for rs in caution.values() for c in rs}
    return {
        "source": "results/t3.json (D-039)",
        "calib_region": region,
        "inherited": inherited,
        "years": sorted(rel),
        "caution_years": caution,
        "reason_codes": {c: t3["reason_codes"][c] for c in sorted(used)},
    }


def _cy(rel: dict) -> list[int]:
    return [int(y) for y in rel["caution_years"]]


def validate_area_doc(doc: dict) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in doc]
    if missing:
        raise ValueError(f"missing keys {missing}")
    n = doc["period"]["n_months"]
    if set(doc["raw"]) != set(PLATFORMS):
        raise ValueError(f"raw must hold exactly {PLATFORMS} (never a platform sum)")
    for k in ("value", "lo", "hi", "source", "partial"):
        if len(doc["harmonized"][k]) != n:
            raise ValueError(f"harmonized.{k} length")
    for p in PLATFORMS:
        if len(doc["raw"][p]["n"]) != n:
            raise ValueError(f"raw.{p} length")
    for k, v in doc["median"].items():
        if len(v["values"]) != 12:
            raise ValueError(f"median.{k}")
    if len(doc["bbox"]) != 4:
        raise ValueError("bbox")


# ------------------------------------------------------------------ geometry


def _round_coords(geom: dict, nd: int = COORD_DECIMALS) -> dict:
    def rc(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], nd), round(c[1], nd)]
        return [rc(x) for x in c]

    return {"type": geom["type"], "coordinates": rc(geom["coordinates"])}


def _bbox(g) -> list[float]:
    return [round(v, 4) for v in g.bounds]


def district_meta(boundaries_dir: Path, shape_ids: set[str]):
    """meta dicts and simplified GeoJSON features for ADM2 shapes in shape_ids."""
    from shapely.geometry import mapping
    from shapely.strtree import STRtree

    from blindspot.boundaries import load_shapes

    shapes = load_shapes(boundaries_dir)
    adm1 = [s for s in shapes if s.level == "ADM1"]
    tree = STRtree([s.geometry for s in adm1])
    metas, feats = {}, []
    for s in shapes:
        if s.level != "ADM2" or s.shape_id not in shape_ids:
            continue
        pt = s.geometry.representative_point()
        cand = [adm1[i] for i in tree.query(pt) if adm1[i].iso == s.iso]
        hit = [a for a in cand if a.geometry.contains(pt)]
        if not hit:  # nearest same-country ADM1 (boundary mismatch between sources)
            same = [a for a in adm1 if a.iso == s.iso]
            hit = [min(same, key=lambda a: a.geometry.distance(pt))]
        parent = hit[0]
        meta = {
            "id": s.shape_id,
            "level": "ADM2",
            "name": s.name,
            "country": s.iso,
            "adm1": {"id": parent.shape_id, "name": parent.name},
            "bbox": _bbox(s.geometry),
        }
        metas[s.shape_id] = meta
        simp = s.geometry.simplify(SIMPLIFY_TOL_DEG, preserve_topology=True)
        lic = "ODbL-1.0" if s.iso == "IND" else "Public Domain"
        feats.append(
            {
                "type": "Feature",
                "properties": {
                    "id": s.shape_id,
                    "name": s.name,
                    "country": s.iso,
                    "adm1": parent.name,
                    "licence": lic,
                    "attribution": f"geoBoundaries {s.iso} ADM2",
                },
                "geometry": _round_coords(mapping(simp)),
            }
        )
    regions_meta = {}
    for rid, iso in ((PK_PUNJAB, "PAK"), (IN_PUNJAB, "IND")):
        sh = [a for a in adm1 if a.iso == iso and a.name.strip().casefold() == "punjab"][0]
        regions_meta[rid] = {
            "id": rid,
            "level": "CALIB",
            "name": f"Punjab ({iso})",
            "country": iso,
            "adm1": {"id": sh.shape_id, "name": sh.name},
            "bbox": _bbox(sh.geometry),
        }
    b = COVERAGE_BOX
    regions_meta[REST] = {
        "id": REST,
        "level": "CALIB",
        "name": "Rest of coverage box",
        "country": None,
        "adm1": None,
        "bbox": [b.lon_min, b.lat_min, b.lon_max, b.lat_max],
    }
    return metas, feats, regions_meta


# ------------------------------------------------------------------ tiles


def tile_key(lat: float, lon: float) -> tuple[int, int]:
    """1° tile (floor), with the box's upper edge folded into the last tile."""
    b = COVERAGE_BOX
    la = min(math.floor(lat), int(b.lat_max) - 1)
    lo = min(math.floor(lon), int(b.lon_max) - 1)
    return la, lo


TILE_COLUMNS = (
    "lat",
    "lon",
    "acq_date",
    "local_time",
    "platform",
    "instrument",
    "confidence",
    "frp",
    "daynight",
    "adm2_id",
)

# Exact ADM2 shape_id per detection from regions.py point-in-polygon (full-resolution
# polygons), so the district hotspot CSV matches the calendar counts (D-038).
# {src} is an internal view name; the point_regions path is a bound parameter.
ADM2_JOIN_SQL = """
SELECT h.*, r.adm2_id
FROM {src} h
LEFT JOIN (
    SELECT lat, lon, any_value(shape_id) AS adm2_id
    FROM read_parquet(?) WHERE level = 'ADM2' GROUP BY lat, lon
) r ON h.lat = r.lat AND h.lon = r.lon
"""


def write_tiles(processed: Path, out_dir: Path) -> dict:
    from blindspot import ingest, mask

    con = ingest.connect(Path(processed) / "hotspots")
    con.execute("SET enable_progress_bar = false")
    res = mask.load_mask(
        Path(processed) / mask.MASK_CELLS_FILE, Path(processed) / mask.MASK_REPORT_FILE
    )
    mask.apply_mask(con, res)
    from blindspot.regions import POINT_REGIONS_FILE

    pr = Path(processed) / "regions" / POINT_REGIONS_FILE
    con.execute(
        "CREATE TEMP TABLE hotspots_tiles AS " + ADM2_JOIN_SQL.format(src="hotspots_masked"),
        [str(pr)],
    )
    b = COVERAGE_BOX
    tiles_dir = Path(out_dir) / "tiles"
    if tiles_dir.exists():
        shutil.rmtree(tiles_dir)
    years = [
        r[0]
        for r in con.execute(
            "SELECT DISTINCT year(CAST(local_solar_datetime AS DATE)) FROM hotspots_masked "
            "ORDER BY 1"
        ).fetchall()
    ]
    counts: dict[str, dict[str, int]] = {}
    total = 0
    for y in years:
        df = con.execute(
            """
            SELECT lat, lon,
                   CAST(local_solar_datetime AS DATE) AS acq_date,
                   strftime(local_solar_datetime, '%H:%M') AS local_time,
                   platform, instrument, confidence_raw AS confidence,
                   frp, daynight, adm2_id,
                   LEAST(CAST(floor(lat) AS INTEGER), ?) AS tlat,
                   LEAST(CAST(floor(lon) AS INTEGER), ?) AS tlon
            FROM hotspots_tiles
            WHERE year(CAST(local_solar_datetime AS DATE)) = ?
            ORDER BY acq_date, local_time, lat, lon, platform
            """,
            [int(b.lat_max) - 1, int(b.lon_max) - 1, int(y)],
        ).df()
        ydir = tiles_dir / f"year={y}"
        ydir.mkdir(parents=True, exist_ok=True)
        counts[str(y)] = {}
        for (tla, tlo), g in df.groupby(["tlat", "tlon"], sort=True):
            name = f"tile_{tla}_{tlo}.parquet"
            t = pa.Table.from_pandas(g[list(TILE_COLUMNS)], preserve_index=False)
            t = t.set_column(2, "acq_date", t.column("acq_date").cast(pa.date32()))
            pq.write_table(t, ydir / name, compression=TILE_COMPRESSION)
            counts[str(y)][name] = int(len(g))
            total += len(g)
    manifest = {
        "tile_deg": TILE_DEG,
        "path_template": "tiles/year={year}/tile_{lat}_{lon}.parquet",
        "adm2_id": "exact geoBoundaries ADM2 shape_id from regions/point_regions.parquet "
        "(null outside any ADM2), D-038",
        "tile_key": "floor(lat), floor(lon) of the detection; box upper edge folded in",
        "year": "local solar year",
        "columns": list(TILE_COLUMNS),
        "compression": TILE_COMPRESSION,
        "filters": "PLAN.md §4 filters + persistent-hotspot mask (D-024); standard data only",
        "csv_row_cap": CSV_ROW_CAP,
        "n_rows_total": int(total),
        "rows": counts,
    }
    (tiles_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


# ------------------------------------------------------------------ run


def constants() -> dict:
    b = COVERAGE_BOX
    return {
        "schema_version": SCHEMA_VERSION,
        "csv_row_cap": CSV_ROW_CAP,
        "csv_cap_message": "More than {cap} rows: narrow your range.",
        "tile_deg": TILE_DEG,
        "tile_path_template": "tiles/year={year}/tile_{lat}_{lon}.parquet",
        "coverage_box": {
            "lon_min": b.lon_min,
            "lon_max": b.lon_max,
            "lat_min": b.lat_min,
            "lat_max": b.lat_max,
        },
        "platforms": list(PLATFORMS),
        "units": {"harmonized": HARMONIZED_UNIT, "raw": RAW_UNIT},
        "partial_coverage": PARTIAL_COVERAGE,
        "nrt_label": "near-real-time, provisional",
        "scope": (
            "Coverage: Pakistan and northern India. The method should transfer to other regions."
        ),
    }


def calibration_doc(processed: Path, boundaries_dir: Path, prov: dict) -> dict:
    """Factors + Punjab polygons + platform availability for client-side custom-AOI series.

    The browser applies the same splice as calibrate.py (D-027) to tile detections of a drawn
    box or radius (D-036): Aqua x f(region, month) before 2012, S-NPP as observed after.
    Unit: hotspots only (the primary unit, CLAUDE.md rule 2)."""
    import shapely

    from blindspot.boundaries import find_shape, load_shapes
    from blindspot.regions import PUNJAB_NAME

    hdir = Path(processed) / "harmonized"
    fac = pd.read_parquet(hdir / "calibration_factors.parquet")
    fac = fac[fac.unit == "hotspots"]
    factors: dict = {}
    for pair, g in fac.groupby("pair"):
        factors[pair] = {
            r: {
                "factor": [_r(x, 6) for x in gg.sort_values("month")["factor"]],
                "lo": [_r(x, 6) for x in gg.sort_values("month")["lo"]],
                "hi": [_r(x, 6) for x in gg.sort_values("month")["hi"]],
            }
            for r, gg in g.groupby("region")
        }
    shapes = load_shapes(Path(boundaries_dir))
    polys = {}
    for rid, iso in ((PK_PUNJAB, "PAK"), (IN_PUNJAB, "IND")):
        s = find_shape(shapes, iso, "ADM1", PUNJAB_NAME)
        g = s.geometry.simplify(CALIB_POLY_TOL_DEG, preserve_topology=True)
        polys[rid] = _round_coords(json.loads(shapely.to_geojson(g)), CALIB_POLY_DECIMALS)
    pdays = pd.read_parquet(hdir / "platform_days.parquet")
    d = pd.to_datetime(pdays["date"])
    av = pdays.assign(ym=d.dt.strftime("%Y-%m")).groupby(["platform", "ym"]).size()
    avail = {p: {k: int(v) for k, v in av[p].items()} for p in av.index.levels[0]}
    return {
        "schema_version": SCHEMA_VERSION,
        "unit": "hotspots",
        "rule": "D-027 splice: Aqua x f(region, month) up to SNPP_FIRST-1; S-NPP observed "
        "from snpp_first to snpp_last; region of each detection: inside PK Punjab polygon -> "
        "PK_Punjab, else inside IN Punjab polygon -> IN_Punjab, else rest_of_box (D-036)",
        "snpp_first": ym(*SNPP_FIRST_MONTH),
        "snpp_last": ym(*SNPP_LAST_MONTH),
        "factors": factors,
        "punjab_polygons": polys,
        "polygon_simplify_tolerance_deg": CALIB_POLY_TOL_DEG,
        "days_available": avail,
        "provenance": prov,
    }


def nrt_mask_doc(processed: Path) -> dict:
    """Persistent-mask cells for the NRT function (D-010, D-040): integer indices on grid_deg."""
    report = json.loads((processed / "mask_report.json").read_text())
    cols = ["cell_lat", "cell_lon"]
    cells = pq.read_table(processed / "persistent_mask_cells.parquet", columns=cols)
    lat, lon = cells.column("cell_lat").to_pylist(), cells.column("cell_lon").to_pylist()
    pairs = sorted(zip(lat, lon, strict=True))
    return {
        "rule": report["parameters"]["rule"],
        "grid_deg": report["parameters"]["grid_deg"],
        "index_formula": "floor(coord / grid_deg + 1e-9)",
        "cells": [[int(a), int(b)] for a, b in pairs],
    }


def _write_json(path: Path, obj) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    path.write_text(s, encoding="utf-8")
    return len(s.encode())


def run(processed: Path, boundaries: Path, out: Path, repo: Path, tiles: bool = True) -> dict:
    processed, out = Path(processed), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    hdir = processed / "harmonized"
    harm = pd.read_parquet(hdir / "monthly_harmonized.parquet")
    raw = pd.read_parquet(hdir / "monthly_raw.parquet")
    last = last_complete_month(harm)
    prov_full = provenance.collect(
        {
            "harmonized": hdir / "monthly_harmonized.parquet",
            "monthly_raw": hdir / "monthly_raw.parquet",
            "boundaries_manifest": Path(boundaries) / "manifest.json",
        },
        repo,
    )
    prov = {
        "commit": prov_full["code"]["commit"],
        "code_dirty": prov_full["code"]["code_dirty"],
        "inputs_sha256": {k: v["sha256"] for k, v in prov_full["inputs"].items()},
        "generator": "pipeline/blindspot/appdata.py",
    }
    adm2_ids = set(harm.loc[harm.level == "ADM2", "shape_id"])
    metas, feats, rmeta = district_meta(Path(boundaries), adm2_ids)
    hg = dict(tuple(harm.groupby("shape_id")))
    rg = dict(tuple(raw.groupby("shape_id")))
    for d in ("districts", "regions"):
        if (out / d).exists():
            shutil.rmtree(out / d)
    sizes = []
    t3 = json.loads((processed / "results" / "t3.json").read_text())
    for sid, meta in sorted(metas.items()):
        rel = reliability_doc(t3, calib_region_of(meta, rmeta), inherited=True)
        doc = area_doc(meta, hg[sid], rg[sid], last, prov, caution_years=_cy(rel))
        doc["reliability"] = rel
        validate_area_doc(doc)
        sizes.append(_write_json(out / "districts" / f"{sid}.json", doc))
    rsizes = {}
    for rid, fname in REGION_FILES.items():
        rel = reliability_doc(t3, rid, inherited=False)
        doc = area_doc(rmeta[rid], hg[rid], rg[rid], last, prov, caution_years=_cy(rel))
        doc["reliability"] = rel
        validate_area_doc(doc)
        rsizes[fname] = _write_json(out / "regions" / f"{fname}.json", doc)
    gj = {
        "type": "FeatureCollection",
        "attribution": "geoBoundaries gbOpen; PAK ADM2 Public Domain; IND ADM2 ODbL 1.0 "
        "(derived simplified boundaries, share-alike, D-031)",
        "licence_ind": "ODbL-1.0",
        "simplify_tolerance_deg": SIMPLIFY_TOL_DEG,
        "features": feats,
    }
    gj_bytes = _write_json(out / "districts.geojson", gj)
    index = {
        "schema_version": SCHEMA_VERSION,
        "period": {"first": "2003-01", "last": ym(*last)},
        "boundaries": "districts.geojson",
        "regions": {rid: f"regions/{f}.json" for rid, f in REGION_FILES.items()},
        "districts": [
            {k: m[k] for k in ("id", "name", "country", "bbox")} | {"adm1": m["adm1"]["name"]}
            for m in sorted(metas.values(), key=lambda m: (m["country"], m["name"]))
        ],
        "licenses": licenses(),
        "provenance": prov,
    }
    _write_json(out / "index.json", index)
    (out / "constants.json").write_text(json.dumps(constants(), indent=1))
    (out / "ATTRIBUTION.md").write_text(attribution_markdown(), encoding="utf-8")
    rdir = out / "results"
    rdir.mkdir(exist_ok=True)
    for src in (
        processed / "results" / "t1.json",
        processed / "results" / "t2.json",
        processed / "results" / "t3.json",
        processed / "results" / "charts_t2.json",
        processed / "mask_report.json",
    ):
        shutil.copyfile(src, rdir / src.name)
    _write_json(rdir / "calibration.json", calibration_doc(processed, Path(boundaries), prov))
    (out / "nrt").mkdir(exist_ok=True)
    _write_json(out / "nrt" / "mask_cells.json", nrt_mask_doc(processed))
    summary = {
        "n_districts": len(metas),
        "last_month": ym(*last),
        "district_bytes_median": int(pd.Series(sizes).median()),
        "district_bytes_max": int(max(sizes)),
        "region_bytes": rsizes,
        "geojson_bytes": gj_bytes,
    }
    if tiles:
        man = write_tiles(processed, out)
        summary["tile_rows"] = man["n_rows_total"]
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--processed", type=Path, default=Path("data/processed"))
    p.add_argument("--boundaries", type=Path, default=Path("data/raw/boundaries"))
    p.add_argument("--out", type=Path, default=Path("web/public/data"))
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--no-tiles", action="store_true")
    a = p.parse_args(argv)
    print(json.dumps(run(a.processed, a.boundaries, a.out, a.repo, not a.no_tiles), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
