"""T2 sensor consistency (overpass-controlled) and T2b timing shift, as pre-registered in
PLAN.md §4 (definitions: docs/DECISIONS.md D-033). Also the mask report and the T1
re-evaluation.

    python -m blindspot.t2 --hotspots data/processed/hotspots --mask-dir data/processed \
        --regions data/processed/regions --harmonized data/processed/harmonized \
        --t1 data/processed/results/t1.json --out data/processed/results/t2.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from blindspot import calibrate as cal
from blindspot import provenance
from blindspot.regions import REST
from blindspot.t1 import TEST_REGIONS, WINDOW, _json_default

MATCH_TOL_H = 0.5
PI_LEVEL = 0.95
ALPHA, POWER = 0.05, 0.80
CALIB_YEARS = cal.CALIB_YEARS
TEST_YEARS = cal.HELDOUT_YEARS
ALL_YEARS = tuple(range(2012, 2026))
CONTROL = REST
T2_REGIONS = (*TEST_REGIONS, CONTROL)
MIN_MATCHED_DAYS = 10  # D-034 (post-data)
MIN_EVALUABLE_TEST_YEARS = 2  # D-034
DELTA_BINS = (-np.inf, -0.5, 0.0, 0.5, 1.0, 1.5, np.inf)
TERRA_YEARS = tuple(range(2003, 2026))

# ------------------------------------------------------------------ pure functions


def window_days(days: pd.DatetimeIndex, years) -> pd.DatetimeIndex:
    d = pd.DatetimeIndex(days)
    d = d[d.year.isin(list(years))]
    return d[cal.in_window(d, *WINDOW)]


def scene(daily: pd.DataFrame, region: str, platform: str) -> pd.DataFrame:
    """Per date: n_day, n_night, t_day (median local solar hour of day detections)."""
    d = daily[(daily.region == region) & (daily.platform == platform)]
    day = d[d.daynight == "D"].set_index("date")
    night = d[d.daynight == "N"].set_index("date")
    out = pd.DataFrame({"n_day": day["n"], "t_day": day["t_med"]})
    out = out.join(night["n"].rename("n_night"), how="outer")
    out[["n_day", "n_night"]] = out[["n_day", "n_night"]].fillna(0.0)
    out.index = pd.to_datetime(out.index)
    return out


def pair_days(sa: pd.DataFrame, sb: pd.DataFrame, days: pd.DatetimeIndex) -> pd.DataFrame:
    """Per common day: a, b (day counts, zero-filled), ta, tb, delta = ta - tb (hours)."""
    idx = pd.DatetimeIndex(days)
    out = pd.DataFrame(
        {
            "a": sa["n_day"].reindex(idx).fillna(0.0),
            "b": sb["n_day"].reindex(idx).fillna(0.0),
            "ta": sa["t_day"].reindex(idx),
            "tb": sb["t_day"].reindex(idx),
        },
        index=idx,
    )
    out["delta"] = out.ta - out.tb
    out["year"] = out.index.year
    return out


def yearly(p: pd.DataFrame, tol: float | None) -> pd.DataFrame:
    """Per year: ratio a/b, ln ratio, n_days, median delta. tol=None: all common days;
    else matched days (both seen, |delta| <= tol)."""
    q = p if tol is None else p[(p.a > 0) & (p.b > 0) & (p.delta.abs() <= tol + 1e-12)]
    g = q.groupby("year").agg(a=("a", "sum"), b=("b", "sum"), n_days=("a", "size"))
    dl = p.dropna(subset=["delta"]).groupby("year")["delta"].median()
    g["delta_h"] = dl.reindex(g.index)
    g["delta_sample_h"] = q.dropna(subset=["delta"]).groupby("year")["delta"].median()
    g = g[(g.a > 0) & (g.b > 0)]
    g["ratio"] = g.a / g.b
    g["ln_ratio"] = np.log(g.ratio)
    return g


def pi_mean_test(ln: pd.Series, base_years, test_years, level: float = PI_LEVEL) -> dict:
    """Prediction interval for the mean of len(test) new years from the base years."""
    base = ln.reindex(list(base_years)).dropna()
    test = ln.reindex(list(test_years)).dropna()
    n, k = len(base), len(test)
    m, s = float(base.mean()), float(base.std(ddof=1))
    tq = float(stats.t.ppf(0.5 + level / 2, n - 1))
    half = tq * s * math.sqrt(1 / n + 1 / k)
    tm = float(test.mean())
    return {
        "n_base": n,
        "n_test": k,
        "base_mean_ln": m,
        "base_sd_ln": s,
        "t_quantile": tq,
        "pi_ln": [m - half, m + half],
        "pi_ratio": [math.exp(m - half), math.exp(m + half)],
        "test_mean_ln": tm,
        "test_mean_ratio": math.exp(tm),
        "test_vs_base_pct": math.exp(tm - m) - 1,
        "outside": bool(not (m - half <= tm <= m + half)),
    }


def theil_sen(ln: pd.Series, years, level: float = PI_LEVEL) -> dict:
    s = ln.reindex(list(years)).dropna()
    res = stats.theilslopes(s.to_numpy(), s.index.to_numpy(float), alpha=level)
    lo, hi = float(res.low_slope), float(res.high_slope)
    return {
        "years": [int(y) for y in s.index],
        "slope_ln_per_year": float(res.slope),
        "ci95_ln_per_year": [lo, hi],
        "slope_pct_per_year": math.exp(res.slope) - 1,
        "ci95_pct_per_year": [math.exp(lo) - 1, math.exp(hi) - 1],
        "excludes_zero": bool(lo > 0 or hi < 0),
    }


def drift_effect(g: pd.DataFrame, years, ref_years) -> dict:
    """OLS ln_ratio ~ delta_h over `years`; effect per hour and implied per year."""
    s = g.reindex(list(years)).dropna(subset=["ln_ratio", "delta_h"])
    lr = stats.linregress(s.delta_h.to_numpy(), s.ln_ratio.to_numpy())
    tq = float(stats.t.ppf(0.975, len(s) - 2))
    b, se = float(lr.slope), float(lr.stderr)
    ref = float(g.reindex(list(ref_years)).delta_h.dropna().mean())
    implied = {str(int(y)): math.exp(b * (float(r.delta_h) - ref)) - 1 for y, r in s.iterrows()}
    adj = s.ln_ratio - b * (s.delta_h - ref)
    return {
        "years": [int(y) for y in s.index],
        "slope_ln_per_hour": b,
        "slope_se": se,
        "slope_p": float(lr.pvalue),
        "effect_pct_per_hour": math.exp(b) - 1,
        "effect_ci95_pct_per_hour": [math.exp(b - tq * se) - 1, math.exp(b + tq * se) - 1],
        "ref_delta_h_2012_2021": ref,
        "implied_effect_by_year": implied,
        "adjusted_ln_ratio": {str(int(y)): float(v) for y, v in adj.items()},
        "_adj_series": adj,
    }


def mdd(sd: float, n: int, k: int, alpha: float = ALPHA, power: float = POWER) -> dict:
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    d = float(z * sd * math.sqrt(1 / n + 1 / k))
    return {"ln": d, "pct": math.exp(d) - 1, "alpha": alpha, "power": power, "n": n, "k": k}


def night_share(sc: pd.DataFrame, days: pd.DatetimeIndex) -> dict:
    s = sc.reindex(pd.DatetimeIndex(days)).fillna({"n_day": 0.0, "n_night": 0.0})
    g = s.groupby(s.index.year)[["n_day", "n_night"]].sum()
    out = {}
    for y, r in g.iterrows():
        tot = r.n_day + r.n_night
        out[str(int(y))] = {
            "night": float(r.n_night),
            "day": float(r.n_day),
            "share": float(r.n_night / tot) if tot > 0 else None,
            "n_days": int((s.index.year == y).sum()),
        }
    return out


def overpass_by_year(sc: pd.DataFrame, days: pd.DatetimeIndex) -> dict:
    t = sc["t_day"].reindex(pd.DatetimeIndex(days)).dropna()
    g = t.groupby(t.index.year)
    return {str(int(y)): {"median_h": float(v.median()), "n_days": int(len(v))} for y, v in g}


def evaluable_years(gm: pd.DataFrame, ga: pd.DataFrame, test_years, tol: float = MATCH_TOL_H):
    """D-034: per test year, evaluable iff >= MIN_MATCHED_DAYS matched days and
    |all-days median delta| <= tol. Returns {year: {"evaluable", "reason"}}."""
    out = {}
    for y in test_years:
        nd = int(gm.n_days.get(y, 0)) if y in gm.index else 0
        dl = ga.delta_h.get(y) if y in ga.index else None
        reasons = []
        if nd < MIN_MATCHED_DAYS:
            reasons.append(f"{nd} matched days < {MIN_MATCHED_DAYS}")
        if dl is None or pd.isna(dl) or abs(float(dl)) > tol + 1e-12:
            reasons.append("all-days median delta outside tolerance")
        out[str(int(y))] = {
            "evaluable": not reasons,
            "matched_days": nd,
            "reason": "; ".join(reasons) or "ok",
        }
    return out


def revised_verdict(gm: pd.DataFrame, ev: dict) -> dict:
    ok = [int(y) for y, v in ev.items() if v["evaluable"]]
    if len(ok) < MIN_EVALUABLE_TEST_YEARS:
        return {
            "label": "inconclusive",
            "drift": None,
            "evaluable_test_years": ok,
            "pi_test": None,
            "theil_sen": None,
        }
    pi = pi_mean_test(gm.ln_ratio, CALIB_YEARS, ok)
    ts = theil_sen(gm.ln_ratio, [*CALIB_YEARS, *ok])
    drift = bool(pi["outside"] or ts["excludes_zero"])
    return {
        "label": "drift" if drift else "no drift",
        "drift": drift,
        "evaluable_test_years": ok,
        "pi_test": pi,
        "theil_sen": ts,
    }


def delta_bins(p: pd.DataFrame, split: int = 2022) -> list[dict]:
    """Ratio sum(a)/sum(b) by delta bin, days with both sensors seeing fire, per era."""
    q = p[(p.a > 0) & (p.b > 0)].dropna(subset=["delta"]).copy()
    q["bin"] = pd.cut(q.delta, DELTA_BINS)
    q["era"] = np.where(q.year < split, "2012-2021", "2022-2025")
    out = []
    for (bn, era), g in q.groupby(["bin", "era"], observed=True):
        out.append(
            {
                # open-ended bins: null, never Infinity (strict JSON, D-038)
                "bin_lo_h": float(bn.left) if np.isfinite(bn.left) else None,
                "bin_hi_h": float(bn.right) if np.isfinite(bn.right) else None,
                "era": era,
                "n_days": int(len(g)),
                "ratio": float(g.a.sum() / g.b.sum()),
            }
        )
    return out


def day_points(p: pd.DataFrame) -> list[dict]:
    q = p[(p.a > 0) & (p.b > 0)].dropna(subset=["delta"])
    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "delta_h": round(float(r.delta), 3),
            "ratio": round(float(r.a / r.b), 4),
        }
        for d, r in q.iterrows()
    ]


# ------------------------------------------------------------------ data


def daily_scene_sql(con) -> pd.DataFrame:
    df = con.execute(
        """
        SELECT r.shape_id AS region, h.platform, h.daynight,
               CAST(h.local_solar_datetime AS DATE) AS date, count(*) AS n,
               median(hour(h.local_solar_datetime) + minute(h.local_solar_datetime) / 60.0
                      + second(h.local_solar_datetime) / 3600.0) AS t_med
        FROM hotspots_masked h
        JOIN point_regions r ON r.lat = h.lat AND r.lon = h.lon AND r.level = 'CALIB'
        WHERE month(CAST(h.local_solar_datetime AS DATE)) IN (10, 11)
        GROUP BY ALL
        """
    ).df()
    df["date"] = pd.to_datetime(df["date"])
    df["n"] = df["n"].astype(float)
    return df


def mask_window_share(con) -> dict:
    df = con.execute(
        """
        SELECT r.shape_id AS region, h.platform, count(*) AS n_all,
               count(*) FILTER (WHERE m.lat IS NOT NULL) AS n_masked
        FROM hotspots_filtered h
        JOIN point_regions r ON r.lat = h.lat AND r.lon = h.lon AND r.level = 'CALIB'
        LEFT JOIN hotspots_masked m ON m.source_file = h.source_file
             AND m.source_row = h.source_row
        WHERE (month(CAST(h.local_solar_datetime AS DATE)) = 10
               AND day(CAST(h.local_solar_datetime AS DATE)) >= 15)
           OR month(CAST(h.local_solar_datetime AS DATE)) = 11
        GROUP BY ALL
        """
    ).df()
    out: dict = {}
    for _, r in df.iterrows():
        if r.region in TEST_REGIONS:
            out.setdefault(r.region, {})[r.platform] = {
                "detections": int(r.n_all),
                "removed": int(r.n_all - r.n_masked),
                "share_removed": float((r.n_all - r.n_masked) / r.n_all),
            }
    return out


# ------------------------------------------------------------------ analysis


def _rec(g: pd.DataFrame) -> dict:
    return {
        str(int(y)): {
            "aqua": float(r.a),
            "snpp": float(r.b),
            "ratio": float(r.ratio),
            "n_days": int(r.n_days),
            "delta_h": None if pd.isna(r.delta_h) else float(r.delta_h),
            "delta_sample_median_h": None if pd.isna(r.delta_sample_h) else float(r.delta_sample_h),
        }
        for y, r in g.iterrows()
    }


def t2_region(daily: pd.DataFrame, pdays: pd.DataFrame, region: str) -> dict:
    days = window_days(cal.common_days(pdays, cal.AQUA, cal.SNPP), ALL_YEARS)
    p = pair_days(scene(daily, region, cal.AQUA), scene(daily, region, cal.SNPP), days)
    gm, ga = yearly(p, MATCH_TOL_H), yearly(p, None)
    pi = pi_mean_test(gm.ln_ratio, CALIB_YEARS, TEST_YEARS)
    ts = theil_sen(gm.ln_ratio, ALL_YEARS)
    eff = drift_effect(ga, ALL_YEARS, CALIB_YEARS)
    adj = eff.pop("_adj_series")
    drift = bool(pi["outside"] or ts["excludes_zero"])
    ev = evaluable_years(gm, ga, TEST_YEARS)
    return {
        "delta_bins": delta_bins(p),
        "_points": day_points(p),
        "evaluable_test_years": ev,
        "verdict_revised": revised_verdict(gm, ev),
        "matched": {
            "tolerance_h": MATCH_TOL_H,
            "by_year": _rec(gm),
            "years_missing": [y for y in ALL_YEARS if y not in gm.index],
            "pi_test": pi,
            "theil_sen": ts,
        },
        "all_common_days": {
            "by_year": _rec(ga),
            "pi_test": pi_mean_test(ga.ln_ratio, CALIB_YEARS, TEST_YEARS),
            "theil_sen": theil_sen(ga.ln_ratio, ALL_YEARS),
        },
        "aqua_drift_effect": eff,
        "overpass_adjusted_pi_test_descriptive": pi_mean_test(adj, CALIB_YEARS, TEST_YEARS),
        "min_detectable_drift": mdd(pi["base_sd_ln"], pi["n_base"], len(TEST_YEARS)),
        "verdict": {
            "drift": drift,
            "pi_outside": pi["outside"],
            "theil_sen_excludes_zero": ts["excludes_zero"],
            "label": "drift" if drift else "no drift",
            "rule": "D-033 (pre-registered)",
        },
    }


def t2b_region(daily: pd.DataFrame, pdays: pd.DataFrame, region: str, b: float, ref: float):
    out: dict = {"night_share": {}, "overpass_h": {}}
    for plat in (cal.SNPP, cal.NOAA20):
        avail = pd.DatetimeIndex(pd.to_datetime(pdays.loc[pdays.platform == plat, "date"]))
        out["night_share"][plat] = night_share(
            scene(daily, region, plat), window_days(avail, ALL_YEARS)
        )
    for plat in (cal.AQUA, cal.TERRA, cal.SNPP, cal.NOAA20):
        avail = pd.DatetimeIndex(pd.to_datetime(pdays.loc[pdays.platform == plat, "date"]))
        out["overpass_h"][plat] = overpass_by_year(
            scene(daily, region, plat), window_days(avail, TERRA_YEARS)
        )
    days = window_days(cal.common_days(pdays, cal.TERRA, cal.AQUA), TERRA_YEARS)
    p = pair_days(scene(daily, region, cal.TERRA), scene(daily, region, cal.AQUA), days)
    g = yearly(p, None)
    # Aqua - S-NPP delta per year from T2 drives the correction of Aqua (D-033).
    sdays = window_days(cal.common_days(pdays, cal.AQUA, cal.SNPP), ALL_YEARS)
    pa = pair_days(scene(daily, region, cal.AQUA), scene(daily, region, cal.SNPP), sdays)
    dA = pa.dropna(subset=["delta"]).groupby("year")["delta"].median()
    ta = {}
    for y, r in g.iterrows():
        corr = b * (float(dA[y]) - ref) if y in dA.index else 0.0
        ta[str(int(y))] = {
            "terra": float(r.a),
            "aqua": float(r.b),
            "ratio": float(r.ratio),
            "ratio_corrected": math.exp(float(r.ln_ratio) + corr),
            "corrected": bool(y in dA.index),
            "n_days": int(r.n_days),
        }
    out["terra_aqua"] = ta
    out["correction"] = (
        "ln(T/A)_corr = ln(T/A) + b*(Delta_y - mean Delta_2012-2021), b = T2 Aqua-drift slope; "
        "Terra drift not corrected (D-033)"
    )
    return out


def reevaluate_t1(t1: dict, t2v: dict) -> dict:
    """t2v[r]['label'] in drift / no drift / inconclusive (revised T2, D-034)."""
    out = {}
    for r, v in t1["verdict_primary"].items():
        lab = t2v[r]["label"]
        if lab != "no drift":
            out[r] = {
                "step_pass": v["step_pass"],
                "heldout": f"not judged (T2 {lab})",
                "label": f"{'pass' if v['step_pass'] else 'fail'} (2012 step only; "
                f"held-out not judged because T2 is {lab})",
                "heldout_pass_raw": v["heldout_pass"],
                "pass": bool(v["step_pass"]),
                "basis": "2012 step only (PLAN §4 conditional)",
            }
        else:
            out[r] = {
                "step_pass": v["step_pass"],
                "heldout": "judged",
                "heldout_pass_raw": v["heldout_pass"],
                "pass": bool(v["step_pass"] and v["heldout_pass"]),
                "basis": "2012 step and held-out (T2 found no drift)",
                "label": f"{'pass' if v['step_pass'] and v['heldout_pass'] else 'fail'} "
                f"(2012 step {'pass' if v['step_pass'] else 'fail'}; held-out judged because "
                f"T2 is no drift: {'pass' if v['heldout_pass'] else 'fail'})",
            }
        out[r]["status"] = "final (T2 run)"
    return out


def run(daily, pdays, mask_report, mask_window, t1, provenance_rec) -> dict:
    t2 = {r: t2_region(daily, pdays, r) for r in T2_REGIONS}
    t2b = {}
    for r in T2_REGIONS:
        e = t2[r]["aqua_drift_effect"]
        t2b[r] = t2b_region(daily, pdays, r, e["slope_ln_per_hour"], e["ref_delta_h_2012_2021"])
    charts = {
        "note": "Data for web charts (D-034). Overpass = median local solar hour of daytime "
        "detections; points = one day with both Aqua and S-NPP daytime fire.",
        "overpass_by_year": {r: t2b[r]["overpass_h"] for r in T2_REGIONS},
        "ratio_vs_delta": {r: t2[r].pop("_points") for r in T2_REGIONS},
    }
    t2v = {r: t2[r]["verdict"] for r in TEST_REGIONS}
    t2v_rev = {r: t2[r]["verdict_revised"] for r in TEST_REGIONS}
    return {
        "test": "T2/T2b (PLAN.md §4; definitions docs/DECISIONS.md D-033)",
        "generated": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "regions": list(TEST_REGIONS),
        "control_region": CONTROL,
        "control_note": "rest_of_box: control, post hoc (D-034); no pre-registered verdict",
        "window": {"start": "10-15", "end": "11-30", "time_basis": "local solar date"},
        "parameters": {
            "match_tolerance_h": MATCH_TOL_H,
            "calib_years": list(CALIB_YEARS),
            "test_years": list(TEST_YEARS),
            "pi_level": PI_LEVEL,
            "alpha": ALPHA,
            "power": POWER,
            "detections": "daytime (daynight = D) for ratios",
            "seeds": "none used (no resampling in T2/T2b)",
            "min_matched_days_d034": MIN_MATCHED_DAYS,
            "min_evaluable_test_years_d034": MIN_EVALUABLE_TEST_YEARS,
        },
        "crossing_time_source": {
            "official_per_year_table": False,
            "used": "empirical median local solar time of daytime detections (D-033)",
            "official_milestones": [
                "https://modis-land.gsfc.nasa.gov/news.html",
                "https://www.earthdata.nasa.gov/news/feature-articles/aqua-turns-20",
            ],
        },
        "t2": t2,
        "t2b": t2b,
        "verdict_t2": t2v,
        "verdict_t2_revised": t2v_rev,
        "t1_reevaluated": reevaluate_t1(t1, t2v_rev),
        "t1_reevaluated_d033": reevaluate_t1(t1, t2v),
        "_charts": charts,
        "mask_report": {
            "share_removed_by_platform_all": mask_report["share_removed_by_platform"],
            "n_masked_cells": mask_report["n_masked_cells"],
            "window_by_region": mask_window,
        },
        "provenance": provenance_rec,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument("--mask-dir", type=Path, default=Path("data/processed"))
    p.add_argument("--regions", type=Path, default=Path("data/processed/regions"))
    p.add_argument("--harmonized", type=Path, default=Path("data/processed/harmonized"))
    p.add_argument("--t1", type=Path, default=Path("data/processed/results/t1.json"))
    p.add_argument("--out", type=Path, default=Path("data/processed/results/t2.json"))
    a = p.parse_args(argv)
    con = cal.connect_masked(a.hotspots, a.mask_dir, a.regions)
    daily = daily_scene_sql(con)
    mw = mask_window_share(con)
    pdays = pd.read_parquet(a.harmonized / cal.PLATFORM_DAYS_FILE)
    inputs = {
        "hotspots": a.hotspots,
        "mask_cells": a.mask_dir / "persistent_mask_cells.parquet",
        "mask_report": a.mask_dir / "mask_report.json",
        "point_regions": a.regions / "point_regions.parquet",
        "platform_days": a.harmonized / cal.PLATFORM_DAYS_FILE,
        "t1_json": a.t1,
    }
    out = run(
        daily,
        pdays,
        json.loads((a.mask_dir / "mask_report.json").read_text()),
        mw,
        json.loads(a.t1.read_text()),
        provenance.collect(inputs, Path(".")),
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    charts = out.pop("_charts")
    a.out.write_text(json.dumps(out, indent=2, default=_json_default, allow_nan=False))
    cpath = a.out.parent / "charts_t2.json"
    cpath.write_text(
        json.dumps(charts, separators=(",", ":"), default=_json_default, allow_nan=False)
    )
    for r, v in out["verdict_t2"].items():
        print(f"{r}: T2 {v['label']} (D-033); revised {out['verdict_t2_revised'][r]['label']}")
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
