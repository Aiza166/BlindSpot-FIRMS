"""Calibration factors, splice and harmonized monthly series (PLAN.md §4; D-026, D-027, D-029).

* Days, months and years are local solar (`CAST(local_solar_datetime AS DATE)`).
* Every series is masked with the persistent-hotspot mask exactly as `mask.py` applies it
  (`mask.load_mask` + `mask.apply_mask`).
* Aqua MODIS -> S-NPP VIIRS factor per calibration region x calendar month, ratio of totals
  over 2012-2021 on common available days, bootstrap by year.
* NOAA-20 -> S-NPP factor the same way on 2019-2025 (PLAN §4), intersected with years present.
* Splice: 2003-2011 Aqua x factor; 2012-01..2026-10 S-NPP observed; later NOAA-20 x factor.
  Platforms are never added together (CLAUDE.md rule 1).

    python -m blindspot.calibrate --hotspots data/processed/hotspots --mask-dir data/processed \
        --regions data/processed/regions --out data/processed/harmonized
"""

from __future__ import annotations

import argparse
import calendar
import json
from collections.abc import Iterable
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from blindspot.regions import CALIB_REGIONS, IN_PUNJAB, PK_PUNJAB, REST

AQUA, TERRA, SNPP, NOAA20 = "Aqua", "Terra", "SNPP", "NOAA20"
CALIB_YEARS: tuple[int, ...] = tuple(range(2012, 2022))
HELDOUT_YEARS: tuple[int, ...] = tuple(range(2022, 2026))
NOAA20_FIT_YEARS: tuple[int, ...] = tuple(range(2019, 2026))
FIRST_MONTH = (2003, 1)
SNPP_FIRST_MONTH = (2012, 1)
SNPP_LAST_MONTH = (2026, 10)
GRIDS: tuple[float, ...] = (0.05, 0.1, 0.25)
UNIT_HOTSPOTS = "hotspots"
B_BOOT = 2000
SEED = 20261114
PARTIAL_COVERAGE = 0.9
_EPS = 1e-9

DAILY_FILE = "daily_calib.parquet"
PLATFORM_DAYS_FILE = "platform_days.parquet"
FACTORS_FILE = "calibration_factors.parquet"
MONTHLY_RAW_FILE = "monthly_raw.parquet"
HARMONIZED_FILE = "monthly_harmonized.parquet"
SATURATION_FILE = "saturation.parquet"


def celldays_unit(grid: float) -> str:
    return f"celldays_{grid:g}"


# ------------------------------------------------------------------ pure functions


def common_days(platform_days: pd.DataFrame, a: str, b: str) -> pd.DatetimeIndex:
    """Local dates on which both platforms are available."""
    da = set(pd.to_datetime(platform_days.loc[platform_days.platform == a, "date"]))
    db = set(pd.to_datetime(platform_days.loc[platform_days.platform == b, "date"]))
    return pd.DatetimeIndex(sorted(da & db))


def in_window(dates: pd.Series | pd.DatetimeIndex, start: tuple[int, int], end: tuple[int, int]):
    """True for dates whose (month, day) is within [start, end] (same calendar year)."""
    d = pd.DatetimeIndex(dates)
    md = d.month * 100 + d.day
    return (md >= start[0] * 100 + start[1]) & (md <= end[0] * 100 + end[1])


def pair_totals(
    daily: pd.DataFrame,
    days: pd.DatetimeIndex,
    other: str,
    ref: str,
    years: Iterable[int],
    window: tuple[tuple[int, int], tuple[int, int]] | None = None,
) -> pd.DataFrame:
    """Per region x year x month: `a` = other-platform total, `s` = reference total, both
    over the given common days only (zero-filled), plus `n_days`.

    `daily` has columns region, platform, date, n (one unit only).
    """
    years = sorted(set(years))
    days = pd.DatetimeIndex(days)
    days = days[days.year.isin(years)]
    if window is not None:
        days = days[in_window(days, *window)]
    d = daily.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d[d.date.isin(days) & d.platform.isin([other, ref])]
    d = d.assign(year=d.date.dt.year, month=d.date.dt.month)
    tot = d.pivot_table(
        index=["region", "year", "month"], columns="platform", values="n", aggfunc="sum"
    )
    ndays = pd.Series(1, index=days).groupby([days.year, days.month]).sum()
    ndays.index.names = ["year", "month"]
    regions = sorted(daily["region"].unique())
    idx = pd.MultiIndex.from_tuples(
        [(r, y, m) for r in regions for (y, m) in ndays.index], names=["region", "year", "month"]
    )
    tot = tot.reindex(idx).fillna(0.0)
    out = pd.DataFrame(
        {
            "a": tot.get(other, 0.0),
            "s": tot.get(ref, 0.0),
        },
        index=idx,
    ).reset_index()
    out["n_days"] = [int(ndays.loc[(y, m)]) for y, m in zip(out.year, out.month, strict=True)]
    return out


def ratio_of_sums(a: np.ndarray, s: np.ndarray) -> float:
    sa = float(np.sum(a))
    return float(np.sum(s)) / sa if sa > 0 else float("nan")


def bootstrap_ratio(a: np.ndarray, s: np.ndarray, b: int, rng: np.random.Generator) -> np.ndarray:
    """Year bootstrap of sum(s)/sum(a): resample the years (rows) with replacement."""
    a = np.asarray(a, dtype=float)
    s = np.asarray(s, dtype=float)
    idx = rng.integers(0, len(a), size=(b, len(a)))
    sa = a[idx].sum(axis=1)
    ss = s[idx].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sa > 0, ss / sa, np.nan)


def fit_factors(pairs: pd.DataFrame, b: int = B_BOOT, seed: int = SEED) -> pd.DataFrame:
    """Factor per region x month = sum(s)/sum(a) over the years in `pairs`, with a 95%
    year-bootstrap percentile interval. Groups are processed in sorted order with one RNG,
    so the result is fixed by the seed."""
    rng = np.random.default_rng(seed)
    rows = []
    for (region, month), g in pairs.sort_values(["region", "month", "year"]).groupby(
        ["region", "month"], sort=True
    ):
        a, s = g["a"].to_numpy(float), g["s"].to_numpy(float)
        boot = bootstrap_ratio(a, s, b, rng)
        ok = boot[~np.isnan(boot)]
        rows.append(
            {
                "region": region,
                "month": int(month),
                "factor": ratio_of_sums(a, s),
                "lo": float(np.percentile(ok, 2.5)) if len(ok) else float("nan"),
                "hi": float(np.percentile(ok, 97.5)) if len(ok) else float("nan"),
                "n_boot_undefined": int(len(boot) - len(ok)),
                "n_years": int(len(g)),
                "years": [int(y) for y in g["year"]],
                "sum_a": float(a.sum()),
                "sum_s": float(s.sum()),
                "n_days": int(g["n_days"].sum()),
            }
        )
    return pd.DataFrame(rows)


def era_source(
    year: int,
    month: int,
    snpp_first: tuple[int, int] = SNPP_FIRST_MONTH,
    snpp_last: tuple[int, int] = SNPP_LAST_MONTH,
) -> str:
    """Which platform feeds the harmonized series in this month (PLAN §4 splice)."""
    if (year, month) < snpp_first:
        return AQUA
    if (year, month) <= snpp_last:
        return SNPP
    return NOAA20


def harmonize(
    monthly: pd.DataFrame,
    shapes: pd.DataFrame,
    availability: pd.DataFrame,
    f_aqua: pd.DataFrame,
    f_noaa20: pd.DataFrame,
    first_month: tuple[int, int] = FIRST_MONTH,
    snpp_first: tuple[int, int] = SNPP_FIRST_MONTH,
    snpp_last: tuple[int, int] = SNPP_LAST_MONTH,
) -> pd.DataFrame:
    """Harmonized monthly series on the S-NPP-equivalent scale.

    monthly: level, shape_id, calib_region, platform, year, month, n (masked counts).
    shapes: level, shape_id (every shape to emit, zero-filled).
    availability: platform, year, month, days_available.
    f_aqua / f_noaa20: region, month, factor, lo, hi.
    Each output month takes exactly one source platform; for Aqua/NOAA-20 each detection is
    scaled by the factor of its own calibration region.
    """
    avail = availability.set_index(["platform", "year", "month"])["days_available"]
    months = []
    y, m = first_month
    last = max((int(a), int(b)) for a, b in zip(availability.year, availability.month, strict=True))
    while (y, m) <= last:
        src = era_source(y, m, snpp_first, snpp_last)
        days = int(avail.get((src, y, m), 0))
        if days > 0:
            months.append((y, m, src, days))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    grid = pd.DataFrame(months, columns=["year", "month", "source_platform", "days_available"])
    grid = shapes[["level", "shape_id"]].drop_duplicates().merge(grid, how="cross")

    fac = pd.concat(
        [f_aqua.assign(platform=AQUA), f_noaa20.assign(platform=NOAA20)], ignore_index=True
    )[["platform", "region", "month", "factor", "lo", "hi"]].rename(
        columns={"region": "calib_region"}
    )
    mm = monthly.rename(columns={"platform": "source_platform"})
    mm = grid[["level", "shape_id", "year", "month", "source_platform"]].merge(
        mm, on=["level", "shape_id", "year", "month", "source_platform"], how="inner"
    )
    mm = mm.merge(
        fac.rename(columns={"platform": "source_platform"}),
        on=["source_platform", "calib_region", "month"],
        how="left",
    )
    obs = mm.source_platform == SNPP
    for col, fcol in (("value", "factor"), ("value_lo", "lo"), ("value_hi", "hi")):
        mm[col] = np.where(obs, mm["n"], mm["n"] * mm[fcol])
    # A detection whose factor is undefined makes the month undefined (NaN survives sum).
    agg = (
        mm.groupby(["level", "shape_id", "year", "month"])[["n", "value", "value_lo", "value_hi"]]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={"n": "n_source"})
    )
    nan_any = (
        mm.assign(undef=mm["value"].isna())
        .groupby(["level", "shape_id", "year", "month"])["undef"]
        .any()
        .reset_index()
    )
    agg = agg.merge(nan_any, on=["level", "shape_id", "year", "month"], how="left")
    for col in ("value", "value_lo", "value_hi"):
        agg.loc[agg["undef"], col] = np.nan
    out = grid.merge(
        agg.drop(columns="undef"), on=["level", "shape_id", "year", "month"], how="left"
    )
    zero = out["n_source"].isna()
    out.loc[zero, ["n_source", "value", "value_lo", "value_hi"]] = 0.0
    out["days_in_month"] = [
        calendar.monthrange(int(a), int(b))[1] for a, b in zip(out.year, out.month, strict=True)
    ]
    out["coverage"] = out["days_available"] / out["days_in_month"]
    out["partial"] = out["coverage"] < PARTIAL_COVERAGE
    out["unit"] = "S-NPP-equivalent hotspots"
    return out.sort_values(["level", "shape_id", "year", "month"]).reset_index(drop=True)


# ------------------------------------------------------------------ DuckDB builders


def connect_masked(hotspots_dir: Path, mask_dir: Path, regions_dir: Path):
    """DuckDB with hotspots_masked (mask.py) and point_regions registered."""
    from blindspot import ingest, mask

    con = ingest.connect(hotspots_dir)
    con.execute("SET enable_progress_bar = false")
    res = mask.load_mask(
        Path(mask_dir) / mask.MASK_CELLS_FILE, Path(mask_dir) / mask.MASK_REPORT_FILE
    )
    mask.apply_mask(con, res)
    attach_regions(con, Path(regions_dir) / "point_regions.parquet")
    return con


def attach_regions(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    con.read_parquet(str(path)).create_view("point_regions", replace=True)


def platform_days_sql(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Local dates with at least one standard, in-box row per platform (D-026)."""
    return con.execute(
        """
        SELECT DISTINCT platform, CAST(local_solar_datetime AS DATE) AS date
        FROM hotspots WHERE passes_standard AND in_box
        ORDER BY platform, date
        """
    ).df()


def daily_calib_sql(con: duckdb.DuckDBPyConnection, grids: Iterable[float] = GRIDS) -> pd.DataFrame:
    """region, unit, platform, date, n for the calibration regions: hotspot counts and
    cell-days per grid (D-029)."""
    parts = [
        con.execute(
            """
            SELECT r.shape_id AS region, $unit AS unit, h.platform,
                   CAST(h.local_solar_datetime AS DATE) AS date, count(*) AS n
            FROM hotspots_masked h
            JOIN point_regions r ON r.lat = h.lat AND r.lon = h.lon AND r.level = 'CALIB'
            GROUP BY ALL
            """,
            {"unit": UNIT_HOTSPOTS},
        ).df()
    ]
    for g in grids:
        parts.append(
            con.execute(
                """
                SELECT region, $unit AS unit, platform, date,
                       count(DISTINCT (cell_lat, cell_lon)) AS n
                FROM (
                    SELECT r.shape_id AS region, h.platform,
                           CAST(h.local_solar_datetime AS DATE) AS date,
                           CAST(floor(h.lat / $grid + $eps) AS BIGINT) AS cell_lat,
                           CAST(floor(h.lon / $grid + $eps) AS BIGINT) AS cell_lon
                    FROM hotspots_masked h
                    JOIN point_regions r
                      ON r.lat = h.lat AND r.lon = h.lon AND r.level = 'CALIB'
                )
                GROUP BY ALL
                """,
                {"unit": celldays_unit(g), "grid": float(g), "eps": _EPS},
            ).df()
        )
    out = pd.concat(parts, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    out["n"] = out["n"].astype("int64")
    return out


def saturation_sql(
    con: duckdb.DuckDBPyConnection, days: pd.DatetimeIndex, grids: Iterable[float] = GRIDS
) -> pd.DataFrame:
    """Per region x grid x year-month over common Aqua/S-NPP days: cell-days with both
    active / cell-days with either active (D-029)."""
    con.register("_common_days", pd.DataFrame({"date": pd.DatetimeIndex(days).date}))
    parts = []
    for g in grids:
        parts.append(
            con.execute(
                """
                WITH c AS (
                    SELECT r.shape_id AS region,
                           CAST(h.local_solar_datetime AS DATE) AS date,
                           CAST(floor(h.lat / $grid + $eps) AS BIGINT) AS cell_lat,
                           CAST(floor(h.lon / $grid + $eps) AS BIGINT) AS cell_lon,
                           bool_or(h.platform = 'Aqua') AS a,
                           bool_or(h.platform = 'SNPP') AS s
                    FROM hotspots_masked h
                    JOIN point_regions r
                      ON r.lat = h.lat AND r.lon = h.lon AND r.level = 'CALIB'
                    WHERE h.platform IN ('Aqua', 'SNPP')
                    GROUP BY ALL
                )
                SELECT region, $grid AS grid_deg, year(date) AS year, month(date) AS month,
                       count(*) FILTER (WHERE a AND s) AS n_both,
                       count(*) AS n_either
                FROM c WHERE date IN (SELECT date FROM _common_days)
                GROUP BY ALL
                """,
                {"grid": float(g), "eps": _EPS},
            ).df()
        )
    con.unregister("_common_days")
    out = pd.concat(parts, ignore_index=True)
    out["share_saturated"] = out["n_both"] / out["n_either"]
    return out.sort_values(["region", "grid_deg", "year", "month"]).reset_index(drop=True)


def monthly_sql(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """level, shape_id, calib_region, platform, year, month, n for CALIB, ADM1 and ADM2.

    For an ADM shape the calibration region of a detection uses the shape's own country
    (D-025), so each detection has exactly one calib_region inside one shape series."""
    return con.execute(
        f"""
        WITH h AS (
            SELECT platform, lat, lon, CAST(local_solar_datetime AS DATE) AS d
            FROM hotspots_masked
        ),
        pf AS (
            SELECT lat, lon,
                   bool_or(shape_id = '{PK_PUNJAB}') AS pk,
                   bool_or(shape_id = '{IN_PUNJAB}') AS inp
            FROM point_regions WHERE level = 'CALIB' GROUP BY ALL
        ),
        adm AS (
            SELECT a.lat, a.lon, a.level, a.shape_id,
                   CASE WHEN a.shape_iso = 'PAK' AND pf.pk THEN '{PK_PUNJAB}'
                        WHEN a.shape_iso = 'IND' AND pf.inp THEN '{IN_PUNJAB}'
                        ELSE '{REST}' END AS calib_region
            FROM point_regions a JOIN pf USING (lat, lon)
            WHERE a.level IN ('ADM1', 'ADM2')
        ),
        cal AS (
            SELECT lat, lon, level, shape_id, shape_id AS calib_region
            FROM point_regions WHERE level = 'CALIB'
        ),
        r AS (SELECT * FROM adm UNION ALL SELECT * FROM cal)
        SELECT r.level, r.shape_id, r.calib_region, h.platform,
               year(h.d) AS year, month(h.d) AS month, count(*) AS n
        FROM h JOIN r USING (lat, lon)
        GROUP BY ALL
        """  # noqa: S608 - only module constants are interpolated
    ).df()


def monthly_availability(platform_days: pd.DataFrame) -> pd.DataFrame:
    d = pd.to_datetime(platform_days["date"])
    out = (
        platform_days.assign(year=d.dt.year, month=d.dt.month)
        .groupby(["platform", "year", "month"])
        .size()
        .rename("days_available")
        .reset_index()
    )
    return out


def raw_series(monthly: pd.DataFrame, shapes: pd.DataFrame, availability: pd.DataFrame):
    """Per-platform monthly series (each platform alone), zero-filled on available months."""
    tot = monthly.groupby(["level", "shape_id", "platform", "year", "month"], as_index=False)[
        "n"
    ].sum()
    grid = shapes[["level", "shape_id"]].drop_duplicates().merge(availability, how="cross")
    out = grid.merge(tot, on=["level", "shape_id", "platform", "year", "month"], how="left")
    out["n"] = out["n"].fillna(0).astype("int64")
    out["days_in_month"] = [
        calendar.monthrange(int(a), int(b))[1] for a, b in zip(out.year, out.month, strict=True)
    ]
    out["partial"] = out["days_available"] / out["days_in_month"] < PARTIAL_COVERAGE
    return out.sort_values(["level", "shape_id", "platform", "year", "month"]).reset_index(
        drop=True
    )


def fit_all_factors(daily: pd.DataFrame, pdays: pd.DataFrame) -> pd.DataFrame:
    """Aqua->S-NPP (2012-2021) and NOAA-20->S-NPP (2019-2025 ∩ present) for every unit."""
    rows = []
    aq = common_days(pdays, AQUA, SNPP)
    n20 = common_days(pdays, NOAA20, SNPP)
    n20_years = sorted(set(NOAA20_FIT_YEARS) & set(n20.year))
    for unit, d in daily.groupby("unit", sort=True):
        for name, other, days, years in (
            ("Aqua->SNPP", AQUA, aq, CALIB_YEARS),
            ("NOAA20->SNPP", NOAA20, n20, n20_years),
        ):
            if not years:
                continue
            f = fit_factors(pair_totals(d, days, other, SNPP, years))
            rows.append(f.assign(pair=name, unit=unit))
    return pd.concat(rows, ignore_index=True)


def run(hotspots_dir: Path, mask_dir: Path, regions_dir: Path, out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    con = connect_masked(hotspots_dir, mask_dir, regions_dir)
    pdays = platform_days_sql(con)
    pdays["date"] = pd.to_datetime(pdays["date"])
    daily = daily_calib_sql(con)
    factors = fit_all_factors(daily, pdays)
    sat = saturation_sql(con, common_days(pdays, AQUA, SNPP))
    monthly = monthly_sql(con)
    shapes_path = Path(regions_dir) / "shapes.parquet"
    shapes = pd.read_parquet(shapes_path)
    shapes = shapes[shapes.share_area_in_box > 0][["level", "shape_id", "shape_name", "shape_iso"]]
    calib = pd.DataFrame(
        {"level": "CALIB", "shape_id": list(CALIB_REGIONS), "shape_name": list(CALIB_REGIONS)}
    )
    shapes = pd.concat([calib, shapes], ignore_index=True)
    avail = monthly_availability(pdays)
    hot = factors[factors.unit == UNIT_HOTSPOTS]
    harm = harmonize(
        monthly,
        shapes,
        avail,
        hot[hot.pair == "Aqua->SNPP"],
        hot[hot.pair == "NOAA20->SNPP"],
    )
    harm = harm.merge(shapes[["level", "shape_id", "shape_name"]], on=["level", "shape_id"])
    raw = raw_series(monthly, shapes, avail)

    daily.to_parquet(out_dir / DAILY_FILE, index=False)
    pdays.to_parquet(out_dir / PLATFORM_DAYS_FILE, index=False)
    factors.to_parquet(out_dir / FACTORS_FILE, index=False)
    sat.to_parquet(out_dir / SATURATION_FILE, index=False)
    raw.to_parquet(out_dir / MONTHLY_RAW_FILE, index=False)
    harm.to_parquet(out_dir / HARMONIZED_FILE, index=False)
    summary = {
        "n_factor_rows": int(len(factors)),
        "n_harmonized_rows": int(len(harm)),
        "n_raw_rows": int(len(raw)),
        "harmonized_last_month": [
            int(harm.year.max()),
            int(harm[harm.year == harm.year.max()].month.max()),
        ],
    }
    (out_dir / "calibrate_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument("--mask-dir", type=Path, default=Path("data/processed"))
    p.add_argument("--regions", type=Path, default=Path("data/processed/regions"))
    p.add_argument("--out", type=Path, default=Path("data/processed/harmonized"))
    args = p.parse_args(argv)
    print(json.dumps(run(args.hotspots, args.mask_dir, args.regions, args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
