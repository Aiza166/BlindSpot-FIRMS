"""T1 harmonization test, exactly as pre-registered in PLAN.md §4 (definitions: D-028).

(a) 2012 step: raw step = S/A - 1, harmonized step = S/P - 1 in the 2012 window, P with
    factors fit on 2013-2021 only; pass if |harmonized| / |raw| < 0.10.
(b) Held-out: 2022-2025 S-NPP window totals vs the Aqua-predicted totals, 95% prediction
    interval from leave-one-year-out residuals over 2012-2021; pass if all four are inside.
    Judged only if T2 finds no drift, so every verdict is "provisional pending T2".

Regions: PK Punjab and IN Punjab, each alone. Window 15 Oct - 30 Nov, local solar date.
Primary unit: hotspot counts; cell-days on 0.05/0.1/0.25° are robustness only.

    python -m blindspot.t1 --harmonized data/processed/harmonized \
        --out data/processed/results/t1.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from blindspot import calibrate as cal
from blindspot import provenance
from blindspot.regions import IN_PUNJAB, PK_PUNJAB

TEST_REGIONS = (PK_PUNJAB, IN_PUNJAB)
WINDOW = ((10, 15), (11, 30))
WINDOW_MONTHS = (10, 11)
STEP_YEAR = 2012
STEP_FIT_YEARS = tuple(range(2013, 2022))
STEP_THRESHOLD = 0.10
PI_LEVEL = 0.95
STATUS = "provisional pending T2"


def month_factors(pairs_full: pd.DataFrame, years: Iterable[int]) -> dict[int, float]:
    """sum(s)/sum(a) per window month over `years` (full calendar months)."""
    p = pairs_full[pairs_full.year.isin(list(years)) & pairs_full.month.isin(WINDOW_MONTHS)]
    g = p.groupby("month")[["a", "s"]].sum()
    return {int(m): (r.s / r.a if r.a > 0 else float("nan")) for m, r in g.iterrows()}


def _window_year(pairs_window: pd.DataFrame, year: int) -> pd.DataFrame:
    return pairs_window[pairs_window.year == year].set_index("month")


def predicted(pairs_window: pd.DataFrame, year: int, factors: dict[int, float]) -> float:
    w = _window_year(pairs_window, year)
    return float(sum(factors[int(m)] * w.loc[m, "a"] for m in w.index))


def step_test(
    pairs_window: pd.DataFrame,
    pairs_full: pd.DataFrame,
    step_year: int = STEP_YEAR,
    fit_years: Iterable[int] = STEP_FIT_YEARS,
    b: int = cal.B_BOOT,
    seed: int = cal.SEED,
    threshold: float = STEP_THRESHOLD,
) -> dict:
    fit_years = sorted(fit_years)
    w = _window_year(pairs_window, step_year)
    a, s = float(w.a.sum()), float(w.s.sum())
    f = month_factors(pairs_full, fit_years)
    p = predicted(pairs_window, step_year, f)
    raw = s / a - 1
    harm = s / p - 1
    ratio = abs(harm) / abs(raw) if raw != 0 else float("inf")

    # Year bootstrap of the 2013-2021 factors (one draw of years shared by Oct and Nov).
    rng = np.random.default_rng(seed)
    full = pairs_full[pairs_full.month.isin(WINDOW_MONTHS)].set_index(["year", "month"])
    A = np.array([[full.loc[(y, m), "a"] for m in WINDOW_MONTHS] for y in fit_years])
    S = np.array([[full.loc[(y, m), "s"] for m in WINDOW_MONTHS] for y in fit_years])
    wa = np.array([w.loc[m, "a"] if m in w.index else 0.0 for m in WINDOW_MONTHS])
    idx = rng.integers(0, len(fit_years), size=(b, len(fit_years)))
    with np.errstate(divide="ignore", invalid="ignore"):
        fb = S[idx].sum(axis=1) / A[idx].sum(axis=1)  # (b, months)
        pb = (fb * wa).sum(axis=1)
        rb = np.abs(s / pb - 1) / abs(raw)
    rb = rb[np.isfinite(rb)]
    return {
        "year": step_year,
        "fit_years": fit_years,
        "aqua_window_total": a,
        "snpp_window_total": s,
        "aqua_predicted_total": p,
        "factors_used": {str(k): v for k, v in f.items()},
        "raw_step": raw,
        "harmonized_step": harm,
        "ratio": ratio,
        "ratio_ci95": [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))],
        "threshold": threshold,
        "pass": bool(ratio < threshold),
        "n_boot": int(b),
        "seed": int(seed),
    }


def heldout_test(
    pairs_window: pd.DataFrame,
    pairs_full: pd.DataFrame,
    calib_years: Iterable[int] = cal.CALIB_YEARS,
    heldout_years: Iterable[int] = cal.HELDOUT_YEARS,
    level: float = PI_LEVEL,
) -> dict:
    calib_years = sorted(calib_years)
    heldout_years = sorted(heldout_years)
    resid = []
    for y in calib_years:
        f = month_factors(pairs_full, [k for k in calib_years if k != y])
        s = float(_window_year(pairs_window, y).s.sum())
        resid.append(math.log(s / predicted(pairs_window, y, f)))
    e = np.array(resid)
    n = len(e)
    tq = float(stats.t.ppf(0.5 + level / 2, n - 1))
    half = tq * float(e.std(ddof=1)) * math.sqrt(1 + 1 / n)
    lo, hi = float(e.mean()) - half, float(e.mean()) + half
    f_all = month_factors(pairs_full, calib_years)
    years = []
    for y in heldout_years:
        w = _window_year(pairs_window, y)
        s = float(w.s.sum())
        p = predicted(pairs_window, y, f_all)
        ey = math.log(s / p)
        years.append(
            {
                "year": y,
                "observed": s,
                "aqua_window_total": float(w.a.sum()),
                "aqua_predicted": p,
                "predicted_bias_corrected": p * math.exp(float(e.mean())),
                "observed_pi95": [p * math.exp(lo), p * math.exp(hi)],
                "log_residual": ey,
                "inside": bool(lo <= ey <= hi),
            }
        )
    n_in = sum(r["inside"] for r in years)
    return {
        "calib_years": calib_years,
        "heldout_years": heldout_years,
        "factors_used": {str(k): v for k, v in f_all.items()},
        "loyo_log_residuals": {str(y): float(v) for y, v in zip(calib_years, e, strict=True)},
        "residual_mean": float(e.mean()),
        "residual_sd": float(e.std(ddof=1)),
        "t_quantile": tq,
        "pi_level": level,
        "pi_log": [lo, hi],
        "years": years,
        "n": len(years),
        "n_inside": int(n_in),
        "pass": bool(n_in == len(years)),
    }


def verdict(step: dict, held: dict) -> dict:
    return {
        "pass": bool(step["pass"] and held["pass"]),
        "step_pass": bool(step["pass"]),
        "heldout_pass": bool(held["pass"]),
        "status": STATUS,
        "note": (
            "PLAN.md §4: the held-out part is judged only if T2 finds no drift. Re-evaluated "
            "verdict after T2: data/processed/results/t2.json key t1_reevaluated "
            "(docs/RESULTS_T2.md)."
        ),
    }


def _pairs(daily: pd.DataFrame, days: pd.DatetimeIndex, region: str, window) -> pd.DataFrame:
    years = list(cal.CALIB_YEARS) + list(cal.HELDOUT_YEARS)
    p = cal.pair_totals(daily, days, cal.AQUA, cal.SNPP, years, window=window)
    return p[p.region == region]


def run_unit(daily_unit: pd.DataFrame, days: pd.DatetimeIndex, region: str) -> dict:
    pw = _pairs(daily_unit, days, region, WINDOW)
    pf = _pairs(daily_unit, days, region, None)
    step = step_test(pw, pf)
    held = heldout_test(pw, pf)
    return {
        "window_common_days_by_year": {
            str(int(y)): int(n) for y, n in pw.groupby("year")["n_days"].sum().items()
        },
        "step_2012": step,
        "heldout": held,
        "verdict": verdict(step, held),
    }


def _factor_summary(factors: pd.DataFrame) -> list[dict]:
    keep = ["pair", "unit", "region", "month", "factor", "lo", "hi", "n_years", "sum_a", "sum_s"]
    out = factors[keep].sort_values(["pair", "unit", "region", "month"])
    recs = out.to_dict(orient="records")
    for r in recs:
        for k in ("factor", "lo", "hi"):
            r[k] = None if r[k] is None or (isinstance(r[k], float) and math.isnan(r[k])) else r[k]
    return recs


def _saturation_summary(sat: pd.DataFrame) -> list[dict]:
    s = sat[sat.year.isin(cal.CALIB_YEARS)]
    g = s.groupby(["region", "grid_deg", "month"], as_index=False)[["n_both", "n_either"]].sum()
    g["share_saturated"] = g.n_both / g.n_either
    return g.to_dict(orient="records")


def run(harmonized_dir: Path, out_path: Path, inputs: dict[str, Path], repo: Path) -> dict:
    hd = Path(harmonized_dir)
    daily = pd.read_parquet(hd / cal.DAILY_FILE)
    pdays = pd.read_parquet(hd / cal.PLATFORM_DAYS_FILE)
    factors = pd.read_parquet(hd / cal.FACTORS_FILE)
    sat = pd.read_parquet(hd / cal.SATURATION_FILE)
    days = cal.common_days(pdays, cal.AQUA, cal.SNPP)
    units = [cal.UNIT_HOTSPOTS] + [cal.celldays_unit(g) for g in cal.GRIDS]
    results: dict = {}
    for unit in units:
        d = daily[daily.unit == unit]
        results[unit] = {r: run_unit(d, days, r) for r in TEST_REGIONS}
    aq_days = days[days.year.isin(cal.CALIB_YEARS)]
    out = {
        "test": "T1 harmonization (PLAN.md §4; definitions docs/DECISIONS.md D-028)",
        "generated": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "primary_unit": cal.UNIT_HOTSPOTS,
        "regions": list(TEST_REGIONS),
        "window": {"start": "10-15", "end": "11-30", "time_basis": "local solar date"},
        "parameters": {
            "calib_years": list(cal.CALIB_YEARS),
            "heldout_years": list(cal.HELDOUT_YEARS),
            "step_year": STEP_YEAR,
            "step_fit_years": list(STEP_FIT_YEARS),
            "step_threshold": STEP_THRESHOLD,
            "pi_level": PI_LEVEL,
            "bootstrap_b": cal.B_BOOT,
            "seed": cal.SEED,
            "noaa20_fit_years_planned": list(cal.NOAA20_FIT_YEARS),
            "snpp_last_month": list(cal.SNPP_LAST_MONTH),
            "grids_deg": list(cal.GRIDS),
        },
        "common_days": {
            "aqua_snpp_2012_2021": int(len(aq_days)),
            "first": str(days.min().date()) if len(days) else None,
        },
        "results": results,
        "verdict_primary": {r: results[cal.UNIT_HOTSPOTS][r]["verdict"] for r in TEST_REGIONS},
        "calibration_factors": _factor_summary(factors),
        "saturation_2012_2021_by_month": _saturation_summary(sat),
        "provenance": provenance.collect(inputs, repo),
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=_json_default))
    return out


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if math.isnan(o) else float(o)
    raise TypeError(type(o))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--harmonized", type=Path, default=Path("data/processed/harmonized"))
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument("--mask-dir", type=Path, default=Path("data/processed"))
    p.add_argument("--regions", type=Path, default=Path("data/processed/regions"))
    p.add_argument("--boundaries", type=Path, default=Path("data/raw/boundaries"))
    p.add_argument("--out", type=Path, default=Path("data/processed/results/t1.json"))
    args = p.parse_args(argv)
    inputs = {
        "hotspots": args.hotspots,
        "mask_cells": args.mask_dir / "persistent_mask_cells.parquet",
        "mask_report": args.mask_dir / "mask_report.json",
        "boundaries_manifest": args.boundaries / "manifest.json",
        "point_regions": args.regions / "point_regions.parquet",
        "regions_json": args.regions / "regions.json",
        "harmonized": args.harmonized,
    }
    out = run(args.harmonized, args.out, inputs, Path("."))
    for r, v in out["verdict_primary"].items():
        print(
            f"{r}: T1 pass={v['pass']} (step {v['step_pass']}, held-out {v['heldout_pass']})"
            f" [{v['status']}]"
        )
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
