"""Append 2026 to the app data without re-running 2003-2025 (decisions.md W-12).

Everything already tested stays frozen: the persistent-hotspot mask (web/public/data/nrt/
mask_cells.json, the same cells the NRT function uses), the calibration factors
(results/calibration.json), the 2003-2025 medians and T1-T3. Only the new months are added.

    FIRMS_MAP_KEY=... python -m blindspot.download --area-source VIIRS_SNPP_SP ...   (per source)
    python -m blindspot.extend --raw data/raw/firms_2026 --boundaries data/raw/boundaries \\
        --app web/public/data --last 2026-10

Inputs are FIRMS area-API CSVs. Standard (SP) rows get the full PLAN §4 filters; near-real-time
(NRT) rows have no `type` field, so they get confidence + in-box + mask, like the NRT function
(D-010). Months with any NRT row are marked provisional (CLAUDE.md rule 8).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from blindspot import appdata, calibrate, ingest
from blindspot.boundaries import DEFAULT_SETS, load_shapes
from blindspot.regions import CALIB_REGIONS, assign_points

NOT_TESTED = "not_tested"
NOT_TESTED_TEXT = (
    "This year came after the tests were run, so the correction has not been checked for it"
)
_EPS = 1e-9


def ym_tuple(s: str) -> tuple[int, int]:
    y, m = s.split("-")
    return int(y), int(m)


def _next(ymt: tuple[int, int]) -> tuple[int, int]:
    y, m = ymt
    return (y + 1, 1) if m == 12 else (y, m + 1)


# ------------------------------------------------------------------ rows


def load_raw(raw_dir: Path) -> pd.DataFrame:
    files = sorted(Path(raw_dir).rglob("*.csv"))
    parts = [ingest.normalize_file(f) for f in files]
    parts = [p for p in parts if len(p)]
    if not parts:
        raise ValueError(f"no rows under {raw_dir}")
    return pd.concat(parts, ignore_index=True)


def filter_rows(df: pd.DataFrame, year: int, last: tuple[int, int]) -> pd.DataFrame:
    """PLAN §4 filters; NRT rows skip the type filter (no `type` field, D-010). One local year."""
    df = df.drop_duplicates(["platform", "acq_datetime_utc", "lat", "lon"])
    std = df["passes_standard"].astype(bool)
    keep = df["in_box"].astype(bool) & df["passes_conf"].astype(bool)
    keep &= (std & df["passes_type"].astype(bool)) | ~std
    out = df[keep].copy()
    d = pd.to_datetime(out["local_solar_datetime"])
    end = pd.Timestamp(*_next(last), 1)
    return out[(d.dt.year == year) & (d < end)]


def apply_frozen_mask(df: pd.DataFrame, cells: set[tuple[int, int]], grid: float) -> pd.DataFrame:
    """Drop rows in a persistent-hotspot cell (same formula as mask.cell_index)."""
    keys = zip(df["lat"], df["lon"], strict=True)
    hit = [(math.floor(a / grid + _EPS), math.floor(b / grid + _EPS)) in cells for a, b in keys]
    return df[[not h for h in hit]]


def availability(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """platform, year, month, days_available: local dates with any in-box row (D-026; for 2026
    near-real-time rows count too, since the standard archive stops at the end of July)."""
    d = pd.to_datetime(df.loc[df["in_box"].astype(bool), "local_solar_datetime"]).dt.normalize()
    pdays = pd.DataFrame({"platform": df.loc[df["in_box"].astype(bool), "platform"], "date": d})
    pdays = pdays.drop_duplicates()
    pdays = pdays[pdays.date.dt.year == year]
    return calibrate.monthly_availability(pdays)


def provisional_from(df: pd.DataFrame) -> dict[str, str]:
    """First month (YYYY-MM) with any near-real-time row, per platform."""
    nrt = df[~df["passes_standard"].astype(bool)]
    d = pd.to_datetime(nrt["local_solar_datetime"])
    out = {}
    for p, s in d.groupby(nrt["platform"]):
        out[str(p)] = s.min().strftime("%Y-%m")
    return out


# ------------------------------------------------------------------ series


def factors_frames(cal: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    def frame(pair: str) -> pd.DataFrame:
        rows = []
        for region, f in cal["factors"][pair].items():
            for i in range(12):
                rows.append((region, i + 1, f["factor"][i], f["lo"][i], f["hi"][i]))
        return pd.DataFrame(rows, columns=["region", "month", "factor", "lo", "hi"])

    return frame("Aqua->SNPP"), frame("NOAA20->SNPP")


def series(
    rows: pd.DataFrame, points: pd.DataFrame, shapes: pd.DataFrame, avail: pd.DataFrame, cal: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Harmonized and raw monthly series with calibrate.py's own SQL and splice."""
    con = duckdb.connect()
    con.register("hotspots_masked", rows[["platform", "lat", "lon", "local_solar_datetime"]])
    con.register("point_regions", points)
    monthly = calibrate.monthly_sql(con)
    fa, fn = factors_frames(cal)
    y0 = int(avail.year.min())
    harm = calibrate.harmonize(monthly, shapes, avail, fa, fn, first_month=(y0, 1))
    raw = calibrate.raw_series(monthly, shapes, avail)
    return harm, raw


# ------------------------------------------------------------------ documents


def _is_prov(prov: dict[str, str], platform: str | None, y: int, m: int) -> bool:
    start = prov.get(str(platform)) if platform else None
    return bool(start) and appdata.ym(y, m) >= start


def extend_doc(
    doc: dict,
    harm: pd.DataFrame,
    raw: pd.DataFrame,
    last: tuple[int, int],
    prov: dict[str, str],
    extension: dict,
    first_year: int = 2003,
) -> dict:
    """Return a copy of an area document with months up to `last` appended. History unchanged."""
    old_last = ym_tuple(doc["period"]["last"])
    start = _next(old_last)
    have = {(int(y), int(m)) for y, m in zip(harm.year, harm.month, strict=True)}
    if have and (min(have) != start or max(have) > last):
        raise ValueError(f"new months must be contiguous from {appdata.ym(*start)}")
    months = appdata.month_range(start, last)
    out = json.loads(json.dumps(doc))
    n_old = doc["period"]["n_months"]
    hidx = harm.set_index(["year", "month"])

    def hget(col, y, m):
        return hidx[col].get((y, m)) if (y, m) in hidx.index else None

    h = out["harmonized"]
    h.setdefault("provisional", [False] * n_old)
    for y, m in months:
        src = hget("source_platform", y, m)
        h["value"].append(appdata._r(hget("value", y, m)))
        h["lo"].append(appdata._r(hget("value_lo", y, m)))
        h["hi"].append(appdata._r(hget("value_hi", y, m)))
        h["source"].append(str(src) if src is not None else None)
        part = hget("partial", y, m)
        h["partial"].append(bool(part) if part is not None else None)
        h["provisional"].append(_is_prov(prov, src, y, m))
    for p in appdata.PLATFORMS:
        rp = raw[raw.platform == p].set_index(["year", "month"])
        r = out["raw"][p]
        r.setdefault("provisional", [False] * n_old)
        for y, m in months:
            ok = (y, m) in rp.index
            r["n"].append(int(rp["n"].get((y, m))) if ok else None)
            r["partial"].append(bool(rp["partial"].get((y, m))) if ok else None)
            r["provisional"].append(_is_prov(prov, p, y, m) if ok else False)

    out["period"] = {"first": doc["period"]["first"], "last": appdata.ym(*last)}
    out["period"]["n_months"] = n_old + len(months)
    out["eras"] = appdata.eras(last)

    rel = out.get("reliability")
    if rel is not None:
        for y in range(start[0], last[0] + 1):
            ys = str(y)
            if ys not in rel["years"]:
                rel["years"].append(ys)
            rel["caution_years"].setdefault(ys, [])
            if NOT_TESTED not in rel["caution_years"][ys]:
                rel["caution_years"][ys].append(NOT_TESTED)
        rel["reason_codes"][NOT_TESTED] = NOT_TESTED_TEXT

    # Critical period: baseline years are unchanged (full years only), the "this year" line moves.
    all_months = appdata.month_range(ym_tuple(out["period"]["first"]), last)
    full = pd.DataFrame(
        {
            "year": [y for y, _ in all_months],
            "month": [m for _, m in all_months],
            "value": [float("nan") if v is None else v for v in h["value"]],
            "partial": [bool(x) for x in h["partial"]],
        }
    )
    caution = [int(y) for y in (rel or {}).get("caution_years", {})]
    med_ex, crit = appdata.critical_periods(full, caution, last, first_year)
    out["median_excl_flagged"], out["critical"] = med_ex, crit
    out["provenance"] = {**out["provenance"], "extension": extension}
    return out


# ------------------------------------------------------------------ tiles


def write_year_tiles(
    rows: pd.DataFrame, points: pd.DataFrame, app: Path, year: int, prov: dict[str, str]
) -> int:
    adm2 = (
        points[points.level == "ADM2"]
        .groupby(["lat", "lon"], as_index=False)["shape_id"]
        .first()
        .rename(columns={"shape_id": "adm2_id"})
    )
    t = rows.merge(adm2, on=["lat", "lon"], how="left")
    b = ingest.COVERAGE_BOX
    loc = pd.to_datetime(t["local_solar_datetime"])
    df = pd.DataFrame(
        {
            "lat": t["lat"],
            "lon": t["lon"],
            "acq_date": loc.dt.date,
            "local_time": loc.dt.strftime("%H:%M"),
            "platform": t["platform"],
            "instrument": t["instrument"],
            "confidence": t["confidence_raw"],
            "frp": t["frp"],
            "daynight": t["daynight"],
            "adm2_id": t["adm2_id"],
            "tlat": [min(math.floor(v), int(b.lat_max) - 1) for v in t["lat"]],
            "tlon": [min(math.floor(v), int(b.lon_max) - 1) for v in t["lon"]],
        }
    ).sort_values(["acq_date", "local_time", "lat", "lon", "platform"])
    tiles = Path(app) / "tiles"
    ydir = tiles / f"year={year}"
    if ydir.exists():
        for f in ydir.glob("*.parquet"):
            f.unlink()
    ydir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for (tla, tlo), g in df.groupby(["tlat", "tlon"], sort=True):
        name = f"tile_{tla}_{tlo}.parquet"
        tab = pa.Table.from_pandas(g[list(appdata.TILE_COLUMNS)], preserve_index=False)
        tab = tab.set_column(2, "acq_date", tab.column("acq_date").cast(pa.date32()))
        pq.write_table(tab, ydir / name, compression=appdata.TILE_COMPRESSION)
        counts[name] = int(len(g))
    man_path = tiles / "manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["rows"][str(year)] = counts
    man["n_rows_total"] = int(sum(sum(v.values()) for v in man["rows"].values()))
    man["provisional_from"] = prov
    man["filters"] = (
        "PLAN.md §4 filters + persistent-hotspot mask (D-024); standard data, except rows from "
        "the months in provisional_from onward, which are near-real-time (no type filter, D-010)"
    )
    man_path.write_text(json.dumps(man, indent=1), encoding="utf-8")
    return int(len(df))


# ------------------------------------------------------------------ run


def _read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(raw_dir: Path, boundaries: Path, app: Path, last: tuple[int, int]) -> dict:
    app = Path(app)
    index = _read(app / "index.json")
    cal = _read(app / "results" / "calibration.json")
    mask = _read(app / "nrt" / "mask_cells.json")
    old_last = ym_tuple(index["period"]["last"])
    year = _next(old_last)[0]
    if _next(old_last) != (year, 1) or last[0] != year:
        raise ValueError("extend appends one calendar year at a time, from January")

    allrows = load_raw(raw_dir)
    rows = filter_rows(allrows, year, last)
    n_filtered = len(rows)
    rows = apply_frozen_mask(rows, {tuple(c) for c in mask["cells"]}, float(mask["grid_deg"]))
    prov = provisional_from(rows)
    avail = availability(allrows, year)
    avail = avail[(avail.year * 100 + avail.month) <= last[0] * 100 + last[1]]

    points, _ = assign_points(rows[["lat", "lon"]], load_shapes(Path(boundaries), DEFAULT_SETS))
    shapes = pd.concat(
        [
            pd.DataFrame({"level": "CALIB", "shape_id": list(CALIB_REGIONS)}),
            pd.DataFrame({"level": "ADM2", "shape_id": [d["id"] for d in index["districts"]]}),
        ],
        ignore_index=True,
    )
    harm, raw = series(rows, points, shapes, avail, cal)
    harm = harm[(harm.year * 100 + harm.month) <= last[0] * 100 + last[1]]

    extension = {
        "generator": "pipeline/blindspot/extend.py",
        "added": f"{appdata.ym(year, 1)} to {appdata.ym(*last)}",
        "frozen": "mask cells, calibration factors, 2003-2025 medians, T1-T3",
        "provisional_from": prov,
        "retrieved": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
    }
    hg = dict(tuple(harm.groupby("shape_id")))
    rg = dict(tuple(raw.groupby("shape_id")))
    empty_h, empty_r = harm.iloc[0:0], raw.iloc[0:0]
    targets = [(f"districts/{d['id']}.json", d["id"]) for d in index["districts"]]
    targets += [(path, rid) for rid, path in index["regions"].items()]
    for path, sid in targets:
        doc = _read(app / path)
        new = extend_doc(doc, hg.get(sid, empty_h), rg.get(sid, empty_r), last, prov, extension)
        appdata.validate_area_doc(new)
        appdata._write_json(app / path, new)

    av = avail.assign(ym=[appdata.ym(y, m) for y, m in zip(avail.year, avail.month, strict=True)])
    for p, g in av.groupby("platform"):
        cal["days_available"].setdefault(str(p), {}).update(
            {k: int(v) for k, v in zip(g.ym, g.days_available, strict=True)}
        )
    cal["provisional_from"] = prov
    appdata._write_json(app / "results" / "calibration.json", cal)

    cons = _read(app / "constants.json")
    cons["provisional_from"] = prov
    (app / "constants.json").write_text(json.dumps(cons, indent=1), encoding="utf-8")

    n_tiles = write_year_tiles(rows, points, app, year, prov)
    index["period"]["last"] = appdata.ym(*last)
    appdata._write_json(app / "index.json", index)
    return {
        "rows_read": int(len(allrows)),
        "rows_after_filters": int(n_filtered),
        "rows_after_mask": int(len(rows)),
        "tile_rows": n_tiles,
        "provisional_from": prov,
        "last": appdata.ym(*last),
        "areas": len(targets),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--boundaries", type=Path, required=True)
    p.add_argument("--app", type=Path, default=Path("web/public/data"))
    p.add_argument("--last", required=True, help="last month to add, YYYY-MM")
    a = p.parse_args(argv)
    print(json.dumps(run(a.raw, a.boundaries, a.app, ym_tuple(a.last)), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
