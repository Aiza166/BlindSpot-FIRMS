"""T3 explanation tests for the post-2021 Aqua/S-NPP ratio change: Aqua orbit drift (O),
burning moved later in the day (T), real decline in burning (D). Definitions and decision
rules were pre-registered in docs/DECISIONS.md D-039 before this module was run.

    python -m blindspot.t3 --hotspots data/processed/hotspots --mask-dir data/processed \
        --regions data/processed/regions --harmonized data/processed/harmonized \
        --t1 data/processed/results/t1.json --out data/processed/results/t3.json
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
from blindspot import t2 as t2m
from blindspot.t1 import _json_default

REGIONS = t2m.T2_REGIONS
PRE = t2m.CALIB_YEARS
POST = t2m.TEST_YEARS
ALL = t2m.ALL_YEARS
N20_YEARS = tuple(range(2019, 2026))
N20_PRE = (2019, 2020, 2021)
PRE2012 = tuple(range(2003, 2012))
CLOSE_TOL_H = 10 / 60  # strictly below 10 min (D-039)
MIN_CLOSE_DAYS = 10
MIN_EVAL_POST = 2
DRIFT_TOL_H = t2m.MATCH_TOL_H
FLAG_YEARS = tuple(range(2003, 2026))


# ------------------------------------------------------------------ pure functions


def ratio_by_year(sa: pd.DataFrame, sb: pd.DataFrame, days, years) -> pd.DataFrame:
    """Sum a (day+night) / sum b (day+night) per year over `days`."""
    idx = t2m.window_days(pd.DatetimeIndex(days), years)
    a = (sa.n_day + sa.n_night).reindex(idx).fillna(0.0)
    b = (sb.n_day + sb.n_night).reindex(idx).fillna(0.0)
    g = (
        pd.DataFrame({"a": a, "b": b})
        .groupby(idx.year)
        .agg(a=("a", "sum"), b=("b", "sum"), n_days=("a", "size"))
    )
    g = g[(g.a > 0) & (g.b > 0)]
    g["ratio"] = g.a / g.b
    g["ln_ratio"] = np.log(g.ratio)
    return g


def a1_noaa20_snpp(g: pd.DataFrame) -> dict:
    ts = t2m.theil_sen(g.ln_ratio, N20_YEARS)
    return {
        "by_year": {
            str(int(y)): {"noaa20": r.a, "snpp": r.b, "ratio": r.ratio, "n_days": int(r.n_days)}
            for y, r in g.iterrows()
        },
        "theil_sen": ts,
        "stable": not ts["excludes_zero"],
    }


def _pct_change(rec: dict, pre, post, key: str) -> float | None:
    a = [rec[str(y)][key] for y in pre if str(y) in rec]
    b = [rec[str(y)][key] for y in post if str(y) in rec]
    if not a or not b or np.mean(a) == 0:
        return None
    return float(np.mean(b) / np.mean(a) - 1)


def a2_viirs(ns_snpp: dict, ns_n20: dict) -> dict:
    """ns_*: t2.night_share output {year: {night, day, share, n_days}}."""

    def lnc(key):
        return pd.Series({int(y): math.log(v[key] + 1) for y, v in ns_snpp.items()})

    day_pi = t2m.pi_mean_test(lnc("day"), PRE, POST)
    night_pi = t2m.pi_mean_test(lnc("night"), PRE, POST)
    day_fall = bool(day_pi["test_mean_ln"] < day_pi["pi_ln"][0])
    night_fall = bool(night_pi["test_mean_ln"] < night_pi["pi_ln"][0])
    pre_sh = [ns_snpp[str(y)]["share"] for y in PRE if str(y) in ns_snpp]
    post_sh = [ns_snpp[str(y)]["share"] for y in POST if str(y) in ns_snpp]
    pre_sh = [s for s in pre_sh if s is not None]
    post_sh = [s for s in post_sh if s is not None]
    rise = bool(pre_sh and post_sh and float(np.mean(post_sh)) > max(pre_sh))
    return {
        "snpp": ns_snpp,
        "noaa20": ns_n20,
        "snpp_day_pi": day_pi,
        "snpp_night_pi": night_pi,
        "snpp_day_change_pct": math.exp(day_pi["test_mean_ln"] - day_pi["base_mean_ln"]) - 1,
        "snpp_night_change_pct": math.exp(night_pi["test_mean_ln"] - night_pi["base_mean_ln"]) - 1,
        "snpp_night_share_pre_max": max(pre_sh) if pre_sh else None,
        "snpp_night_share_post_mean": float(np.mean(post_sh)) if post_sh else None,
        "noaa20_day_change_pct_vs_2019_21": _pct_change(ns_n20, N20_PRE, POST, "day"),
        "noaa20_night_change_pct_vs_2019_21": _pct_change(ns_n20, N20_PRE, POST, "night"),
        "day_fall": day_fall,
        "night_fall": night_fall,
        "night_share_rise": rise,
    }


def close_days(p: pd.DataFrame, tol: float = CLOSE_TOL_H) -> pd.DataFrame:
    """Usable days: both have daytime fire and |delta| < tol (strict)."""
    return p[(p.a > 0) & (p.b > 0) & (p.delta.abs() < tol)]


def a3_close(p: pd.DataFrame) -> dict:
    q = close_days(p)
    g = q.groupby("year").agg(a=("a", "sum"), b=("b", "sum"), n_days=("a", "size"))
    g = g[(g.a > 0) & (g.b > 0)]
    g["ln_ratio"] = np.log(g.a / g.b)
    by = {
        str(int(y)): {
            "aqua": float(r.a),
            "snpp": float(r.b),
            "ratio": float(math.exp(r.ln_ratio)),
            "usable_days": int(r.n_days),
            "evaluable": bool(y in POST and r.n_days >= MIN_CLOSE_DAYS) if y in POST else None,
        }
        for y, r in g.iterrows()
    }
    for y in ALL:
        by.setdefault(
            str(y),
            {"aqua": 0.0, "snpp": 0.0, "ratio": None, "usable_days": 0, "evaluable": False},
        )
    ok = [y for y in POST if by[str(y)]["evaluable"]]
    if len(ok) < MIN_EVAL_POST:
        pi, shift, direction = None, "insufficient", None
    else:
        pi = t2m.pi_mean_test(g.ln_ratio, PRE, ok)
        shift = "outside" if pi["outside"] else "inside"
        direction = "higher" if pi["test_mean_ln"] > pi["base_mean_ln"] else "lower"
    return {
        "tolerance_h": CLOSE_TOL_H,
        "min_usable_days": MIN_CLOSE_DAYS,
        "by_year": dict(sorted(by.items())),
        "evaluable_post_years": ok,
        "pi_test": pi,
        "close_shift": shift,
        "post_vs_pre": direction,
    }


def a3_curve(p: pd.DataFrame, g_all: pd.DataFrame) -> dict:
    """Daily ln(a/b) ~ delta fit on PRE only; extrapolate to post yearly delta."""
    d = p[(p.a > 0) & (p.b > 0)].dropna(subset=["delta"])
    pre = d[d.year.isin(list(PRE))]
    lr = stats.linregress(pre.delta.to_numpy(), np.log(pre.a / pre.b).to_numpy())
    b = float(lr.slope)
    ref = float(g_all.reindex(list(PRE)).delta_h.dropna().mean())
    base = float(g_all.reindex(list(PRE)).ln_ratio.dropna().mean())
    lo, hi = (float(x) for x in np.quantile(pre.delta, [0.025, 0.975]))
    s = g_all.dropna(subset=["ln_ratio", "delta_h"])
    expected = base + b * (s.delta_h - ref)
    resid = s.ln_ratio - expected
    pi = t2m.pi_mean_test(resid, PRE, POST)
    sufficient = not pi["outside"]
    by = {
        str(int(y)): {
            "observed_ratio": float(math.exp(s.ln_ratio[y])),
            "expected_ratio": float(math.exp(expected[y])),
            "residual_pct": float(math.exp(resid[y]) - 1),
            "delta_h": float(s.delta_h[y]),
            "beyond_pre_daily_range": bool(not (lo <= s.delta_h[y] <= hi)),
        }
        for y in s.index
    }
    return {
        "fit_years": list(PRE),
        "n_days_fit": int(len(pre)),
        "slope_ln_per_hour": b,
        "slope_se": float(lr.stderr),
        "slope_p": float(lr.pvalue),
        "effect_pct_per_hour": math.exp(b) - 1,
        "pre_daily_delta_range_h": [lo, hi],
        "ref_delta_h": ref,
        "by_year": by,
        "residual_pi_test": pi,
        "post_residual_mean_pct": math.exp(pi["test_mean_ln"] - pi["base_mean_ln"]) - 1,
        "orbit_sufficient": bool(sufficient),
        "residual_sign": None
        if sufficient
        else ("positive" if pi["test_mean_ln"] > pi["base_mean_ln"] else "negative"),
    }


def a4_factor_spread(g: pd.DataFrame, harmonized_step: float) -> dict:
    """g: ratio_by_year(S-NPP, Aqua) -> yearly factor."""
    f = g.reindex(list(range(2013, 2022))).dropna(subset=["ratio"])
    sd_ln = float(f.ln_ratio.std(ddof=1))
    step_ln = abs(math.log(1 + harmonized_step))
    return {
        "years": [int(y) for y in f.index],
        "factor_by_year": {str(int(y)): float(v) for y, v in f.ratio.items()},
        "mean": float(f.ratio.mean()),
        "sd": float(f.ratio.std(ddof=1)),
        "cv": float(f.ratio.std(ddof=1) / f.ratio.mean()),
        "sd_ln": sd_ln,
        "harmonized_step_2012": harmonized_step,
        "step_abs_ln": step_ln,
        "step_in_sd": step_ln / sd_ln,
        "step_normal": bool(step_ln <= 2 * sd_ln),
    }


def a5_terra_aqua(g: pd.DataFrame) -> dict:
    s = g.reindex(list(PRE2012)).dropna(subset=["ratio"])
    ts = t2m.theil_sen(s.ln_ratio, PRE2012)
    return {
        "by_year": {
            str(int(y)): {"ratio": float(r.ratio), "n_days": int(r.n_days)} for y, r in s.iterrows()
        },
        "cv": float(s.ratio.std(ddof=1) / s.ratio.mean()),
        "theil_sen": ts,
        "stable": not ts["excludes_zero"],
    }


def verdicts(a1: dict, a2: dict, a3c: dict, a3k: dict) -> dict:
    cs, suff = a3c["close_shift"], a3k["orbit_sufficient"]
    res_pos = a3k["residual_sign"] == "positive"
    if suff and cs != "outside":
        o = "supported"
    elif not suff and cs == "outside":
        o = "not supported"
    else:
        o = "cannot separate"
    if a1["stable"] and a2["day_fall"] and a2["night_fall"]:
        d = "supported"
    elif not a2["day_fall"]:
        d = "not supported"
    else:
        d = "cannot separate"
    close_up = cs == "outside" and a3c["post_vs_pre"] == "higher"
    if a2["night_share_rise"] and not a2["night_fall"] and (res_pos or close_up):
        t = "supported"
    elif not a2["night_share_rise"]:
        t = "not supported"
    else:
        t = "cannot separate"
    pct = lambda x: f"{x * 100:+.1f}%"  # noqa: E731
    facts = {
        "orbit_curve": f"pre-drift curve {'explains' if suff else 'does not explain'} the "
        f"2022-25 ratio (mean residual {pct(a3k['post_residual_mean_pct'])})",
        "close": f"close-overpass (Δ < 10 min) ratio: {cs}"
        + (f" ({a3c['post_vs_pre']} than 2012-21)" if a3c["post_vs_pre"] else ""),
        "a1": f"NOAA-20/S-NPP {'stable' if a1['stable'] else 'trend'} 2019-25 "
        f"(Theil-Sen {pct(a1['theil_sen']['slope_pct_per_year'])}/yr)",
        "day": f"S-NPP day count 2022-25 {pct(a2['snpp_day_change_pct'])} vs 2012-21 "
        f"({'below' if a2['day_fall'] else 'not below'} PI)",
        "night": f"S-NPP night count {pct(a2['snpp_night_change_pct'])} "
        f"({'below' if a2['night_fall'] else 'not below'} PI)",
        "share": f"S-NPP night share 2022-25 mean "
        f"{(a2['snpp_night_share_post_mean'] or 0) * 100:.1f}% vs 2012-21 max "
        f"{(a2['snpp_night_share_pre_max'] or 0) * 100:.1f}%",
    }

    def row(sup, against, v):
        return {"supporting": sup, "against": against, "verdict": v}

    return {
        "O": row(
            [
                facts[k]
                for k in ("orbit_curve", "close")
                if (suff if k == "orbit_curve" else cs != "outside")
            ],
            [
                facts[k]
                for k in ("orbit_curve", "close")
                if not (suff if k == "orbit_curve" else cs != "outside")
            ],
            o,
        ),
        "T": row(
            [
                f
                for f, ok in (
                    (facts["share"], a2["night_share_rise"]),
                    (facts["night"], not a2["night_fall"]),
                    (facts["orbit_curve"], res_pos),
                    (facts["close"], close_up),
                )
                if ok
            ],
            [
                f
                for f, ok in (
                    (facts["share"], a2["night_share_rise"]),
                    (facts["night"], not a2["night_fall"]),
                )
                if not ok
            ],
            t,
        ),
        "D": row(
            [
                f
                for f, ok in (
                    (facts["day"], a2["day_fall"]),
                    (facts["night"], a2["night_fall"]),
                    (facts["a1"], a1["stable"]),
                )
                if ok
            ],
            [
                f
                for f, ok in (
                    (facts["day"], a2["day_fall"]),
                    (facts["night"], a2["night_fall"]),
                    (facts["a1"], a1["stable"]),
                )
                if not ok
            ],
            d,
        ),
    }


def reliability(years, delta_by_year: dict, a4: dict, a5: dict, t_verdict: str) -> dict:
    """Per calendar year: {"harmonization_reliable": yes|caution, "reasons": [...]}."""
    out = {}
    for y in years:
        r = []
        if y < 2012 and not a5["stable"]:
            r.append("pre2012_terra_aqua_trend")
        if y == 2012 and not a4["step_normal"]:
            r.append("splice_step_outside_normal")
        if y >= 2022:
            dl = delta_by_year.get(y)
            if dl is None or abs(dl) > DRIFT_TOL_H + 1e-12:
                r.append("aqua_overpass_drift")
            if t_verdict == "supported":
                r.append("burning_time_shift")
        out[str(y)] = {"harmonization_reliable": "caution" if r else "yes", "reasons": r}
    return out


REASON_TEXT = {
    "pre2012_terra_aqua_trend": "Terra/Aqua ratio trends in 2003-2011, so Aqua x factor may "
    "not be stable before VIIRS",
    "splice_step_outside_normal": "2012 harmonized step exceeds 2 sd of the 2013-21 factor",
    "aqua_overpass_drift": "Aqua's overpass drifted > 30 min later; the Aqua-to-VIIRS factor "
    "cannot be checked this year",
    "burning_time_shift": "part of the burning moved later in the day; 13:30 satellite counts "
    "may understate it (a real decline is not ruled out)",
}


# ------------------------------------------------------------------ analysis


def t3_region(daily, pdays, region: str, harmonized_step: float | None) -> dict:
    sc = {p: t2m.scene(daily, region, p) for p in (cal.AQUA, cal.TERRA, cal.SNPP, cal.NOAA20)}
    g1 = ratio_by_year(
        sc[cal.NOAA20], sc[cal.SNPP], cal.common_days(pdays, cal.NOAA20, cal.SNPP), N20_YEARS
    )
    a1 = a1_noaa20_snpp(g1)
    ns = {}
    for plat, yrs in ((cal.SNPP, ALL), (cal.NOAA20, N20_YEARS)):
        avail = pd.DatetimeIndex(pd.to_datetime(pdays.loc[pdays.platform == plat, "date"]))
        ns[plat] = t2m.night_share(sc[plat], t2m.window_days(avail, yrs))
    a2 = a2_viirs(ns[cal.SNPP], ns[cal.NOAA20])
    days = t2m.window_days(cal.common_days(pdays, cal.AQUA, cal.SNPP), ALL)
    p = t2m.pair_days(sc[cal.AQUA], sc[cal.SNPP], days)
    ga = t2m.yearly(p, None)
    a3c, a3k = a3_close(p), a3_curve(p, ga)
    gf = ratio_by_year(sc[cal.SNPP], sc[cal.AQUA], cal.common_days(pdays, cal.AQUA, cal.SNPP), ALL)
    a4 = a4_factor_spread(gf, harmonized_step) if harmonized_step is not None else None
    tdays = t2m.window_days(cal.common_days(pdays, cal.TERRA, cal.AQUA), PRE2012)
    gt = t2m.yearly(t2m.pair_days(sc[cal.TERRA], sc[cal.AQUA], tdays), None)
    a5 = a5_terra_aqua(gt)
    v = verdicts(a1, a2, a3c, a3k)
    dmap = {int(y): float(d) for y, d in ga.delta_h.dropna().items()}
    a4_for_flag = a4 or {"step_normal": True}
    flags = reliability(FLAG_YEARS, dmap, a4_for_flag, a5, v["T"]["verdict"])
    return {
        "a1_noaa20_snpp": a1,
        "a2_viirs_only": a2,
        "a3_close_overpass": a3c,
        "a3_orbit_curve": a3k,
        "a4_factor_spread": a4,
        "a5_terra_aqua_pre2012": a5,
        "evidence": v,
        "reliability": flags,
    }


def run(daily, pdays, t1: dict, prov: dict) -> dict:
    steps = {r: v["step_2012"]["harmonized_step"] for r, v in t1["results"]["hotspots"].items()}
    res = {r: t3_region(daily, pdays, r, steps.get(r)) for r in REGIONS}
    return {
        "test": "T3 explanation tests O/T/D (docs/DECISIONS.md D-039, pre-registered)",
        "generated": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "regions": list(REGIONS),
        "control_region": t2m.CONTROL,
        "window": {"start": "10-15", "end": "11-30", "time_basis": "local solar date"},
        "parameters": {
            "pre_years": list(PRE),
            "post_years": list(POST),
            "close_tolerance_h": CLOSE_TOL_H,
            "min_close_days": MIN_CLOSE_DAYS,
            "drift_tolerance_h": DRIFT_TOL_H,
            "a4_note": "factor = S-NPP/Aqua day+night detections on common days (scene table); "
            "no a4 for rest_of_box (no T1 step)",
        },
        "reason_codes": REASON_TEXT,
        "district_inheritance": "districts take the flags of their calibration region: ADM1 PK "
        "Punjab -> PK_Punjab, IN Punjab -> IN_Punjab, else rest_of_box (D-039)",
        "t3": res,
        "provenance": prov,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    ap.add_argument("--mask-dir", type=Path, default=Path("data/processed"))
    ap.add_argument("--regions", type=Path, default=Path("data/processed/regions"))
    ap.add_argument("--harmonized", type=Path, default=Path("data/processed/harmonized"))
    ap.add_argument("--t1", type=Path, default=Path("data/processed/results/t1.json"))
    ap.add_argument("--out", type=Path, default=Path("data/processed/results/t3.json"))
    ap.add_argument("--md", type=Path, default=Path("docs/RESULTS_T3.md"))
    a = ap.parse_args(argv)
    con = cal.connect_masked(a.hotspots, a.mask_dir, a.regions)
    daily = t2m.daily_scene_sql(con)
    pdays = pd.read_parquet(a.harmonized / cal.PLATFORM_DAYS_FILE)
    inputs = {
        "hotspots": a.hotspots,
        "mask_cells": a.mask_dir / "persistent_mask_cells.parquet",
        "point_regions": a.regions / "point_regions.parquet",
        "platform_days": a.harmonized / cal.PLATFORM_DAYS_FILE,
        "t1_json": a.t1,
    }
    out = run(daily, pdays, json.loads(a.t1.read_text()), provenance.collect(inputs, Path(".")))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2, default=_json_default, allow_nan=False))
    a.md.write_text(render_md(json.loads(a.out.read_text())))
    for r, v in out["t3"].items():
        print(r, {k: x["verdict"] for k, x in v["evidence"].items()})
    print(f"-> {a.out}")
    return 0


# ------------------------------------------------------------------ report


def _pc(x) -> str:
    return "n/a" if x is None else f"{x * 100:+.1f}%"


def _r3(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


NAMES = {"PK_Punjab": "PK Punjab", "IN_Punjab": "IN Punjab", "rest_of_box": "Rest of box (control)"}


def render_md(out: dict) -> str:
    L = [
        "# T3 results: orbit drift (O), later burning (T), real decline (D)",
        "",
        f"Generated by `python -m blindspot.t3` from `data/processed/results/t3.json` "
        f"({out['generated']}). Do not edit by hand. Definitions and decision rules: "
        "`docs/DECISIONS.md` D-039 (pre-registered, committed before this was run). "
        "Window 15 Oct–30 Nov, local solar date; masked, filtered detections.",
        "",
        "## Evidence table",
        "",
        "| Region | Explanation | Supporting | Against | Verdict |",
        "|---|---|---|---|---|",
    ]
    lab = {"O": "O: Aqua orbit drift", "T": "T: burning later in the day", "D": "D: real decline"}
    for r, v in out["t3"].items():
        for e in ("O", "T", "D"):
            x = v["evidence"][e]
            L.append(
                f"| {NAMES[r]} | {lab[e]} | {'; '.join(x['supporting']) or '—'} | "
                f"{'; '.join(x['against']) or '—'} | **{x['verdict']}** |"
            )
    L += [
        "",
        "_rest_of_box is a control (post hoc, D-034); its verdicts are diagnostics for the "
        "method, not findings._",
        "",
    ]
    for r, v in out["t3"].items():
        a1, a2 = v["a1_noaa20_snpp"], v["a2_viirs_only"]
        c, k = v["a3_close_overpass"], v["a3_orbit_curve"]
        a4, a5 = v["a4_factor_spread"], v["a5_terra_aqua_pre2012"]
        L += [f"## {NAMES[r]}", ""]
        L += [
            f"**A1 NOAA-20/S-NPP** (day + night, common days): "
            f"{'stable' if a1['stable'] else 'trend'}; Theil–Sen "
            f"{_pc(a1['theil_sen']['slope_pct_per_year'])}/yr "
            f"(95% CI {_pc(a1['theil_sen']['ci95_pct_per_year'][0])} to "
            f"{_pc(a1['theil_sen']['ci95_pct_per_year'][1])}).",
            "",
            f"**A2 VIIRS-only:** S-NPP day count 2022–25 {_pc(a2['snpp_day_change_pct'])} vs "
            f"2012–21 (day_fall={a2['day_fall']}); night count "
            f"{_pc(a2['snpp_night_change_pct'])} (night_fall={a2['night_fall']}); night share "
            f"2022–25 mean {a2['snpp_night_share_post_mean'] * 100:.2f}% vs 2012–21 max "
            f"{a2['snpp_night_share_pre_max'] * 100:.2f}% "
            f"(night_share_rise={a2['night_share_rise']}). NOAA-20 vs 2019–21: day "
            f"{_pc(a2['noaa20_day_change_pct_vs_2019_21'])}, night "
            f"{_pc(a2['noaa20_night_change_pct_vs_2019_21'])} (not used in a rule).",
            "",
            f"**A3 close overpass** (|Δ| < 10 min, ≥ {c['min_usable_days']} usable days): "
            f"{c['close_shift']}; evaluable post years {c['evaluable_post_years'] or 'none'}.",
            "",
            f"**A3 pre-drift curve:** daily ln(Aqua/S-NPP) on Δ, 2012–21 only "
            f"({k['n_days_fit']} days): {_pc(k['effect_pct_per_hour'])} per hour "
            f"(p = {k['slope_p']:.3f}); pre daily Δ range (2.5–97.5%) "
            f"{k['pre_daily_delta_range_h'][0]:.2f} to {k['pre_daily_delta_range_h'][1]:.2f} h. "
            f"2022–25 mean residual {_pc(k['post_residual_mean_pct'])} → "
            f"{'orbit sufficient' if k['orbit_sufficient'] else 'residual remains'}.",
            "",
            "| Year | S-NPP day | S-NPP night | Night share | NOAA-20 day | NOAA-20 night | "
            "N20/S-NPP | Close ratio (days) | Δ all days (h) | Expected ratio | Observed ratio |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for y in ALL:
            s = a2["snpp"].get(str(y), {})
            n = a2["noaa20"].get(str(y), {})
            a = a1["by_year"].get(str(y), {})
            cy = c["by_year"].get(str(y), {})
            ky = k["by_year"].get(str(y), {})
            sh = s.get("share")
            ext = " ‡" if ky.get("beyond_pre_daily_range") else ""
            L.append(
                f"| {y} | {s.get('day', 0):,.0f} | {s.get('night', 0):,.0f} | "
                f"{'n/a' if sh is None else f'{sh * 100:.2f}%'} | "
                f"{n['day']:,.0f} | {n['night']:,.0f} | "
                if n
                else f"| {y} | {s.get('day', 0):,.0f} | {s.get('night', 0):,.0f} | "
                f"{'n/a' if sh is None else f'{sh * 100:.2f}%'} | n/a | n/a | "
            )
            L[-1] += (
                f"{_r3(a.get('ratio'))} | {_r3(cy.get('ratio'))} ({cy.get('usable_days', 0)}) | "
                f"{ky.get('delta_h', float('nan')):.2f} | {_r3(ky.get('expected_ratio'))}{ext} | "
                f"{_r3(ky.get('observed_ratio'))} |"
            )
        L += ["", "‡ Δ beyond the 2012–21 daily range: extrapolated.", ""]
        if a4:
            L += [
                f"**A4 factor spread 2013–21:** S-NPP/Aqua mean {a4['mean']:.2f}, CV "
                f"{a4['cv'] * 100:.1f}%, sd(ln) {a4['sd_ln']:.3f}. 2012 harmonized step "
                f"{_pc(a4['harmonized_step_2012'])} = {a4['step_in_sd']:.2f} sd(ln) → "
                f"{'within normal variation' if a4['step_normal'] else 'outside 2 sd'}.",
                "",
            ]
        L += [
            f"**A5 Terra/Aqua 2003–11:** CV {a5['cv'] * 100:.1f}%; Theil–Sen "
            f"{_pc(a5['theil_sen']['slope_pct_per_year'])}/yr (95% CI "
            f"{_pc(a5['theil_sen']['ci95_pct_per_year'][0])} to "
            f"{_pc(a5['theil_sen']['ci95_pct_per_year'][1])}) → "
            f"{'stable' if a5['stable'] else 'trend'}.",
            "",
            "**A7 reliability flags (caution years):** "
            + (
                ", ".join(
                    f"{y} ({'+'.join(f['reasons'])})"
                    for y, f in v["reliability"].items()
                    if f["reasons"]
                )
                or "none"
            ),
            "",
        ]
    ctl = out["t3"].get(t2m.CONTROL)
    if ctl and "IN_Punjab" in out["t3"]:
        i = out["t3"]["IN_Punjab"]["a2_viirs_only"]
        pre_n = [i["snpp"][str(y)]["night"] for y in PRE if str(y) in i["snpp"]]
        post_n = [i["snpp"][str(y)]["night"] for y in POST if str(y) in i["snpp"]]
        pre_d = [i["snpp"][str(y)]["day"] for y in PRE if str(y) in i["snpp"]]
        post_d = [i["snpp"][str(y)]["day"] for y in POST if str(y) in i["snpp"]]
        L += [
            "## Caveats (numbers from t3.json)",
            "",
            f"- IN Punjab night counts are small: S-NPP night mean {np.mean(pre_n):,.0f} per "
            f"window in 2012–21 vs {np.mean(post_n):,.0f} in 2022–25, while day counts fell "
            f"from {np.mean(pre_d):,.0f} to {np.mean(post_d):,.0f}. The night rise is far too "
            "small to offset the day fall, so a real decline (D) and a later-burning shift (T) "
            "can both be present; the rules can say T is supported, not that D is absent.",
            f"- The pre-drift curve misses the control: rest_of_box 2022–25 mean residual "
            f"{_pc(ctl['a3_orbit_curve']['post_residual_mean_pct'])} (the curve predicts a "
            "rise the control does not show). The curve is fit on natural day-to-day Δ, "
            "which mostly reflects VIIRS swath position, not Aqua's clock time, so the "
            "orbit extrapolation is a weak instrument; compare each region's residual with "
            "the control's.",
        ]
        if all(v["a3_close_overpass"]["close_shift"] == "insufficient" for v in out["t3"].values()):
            L.append(
                f"- No region has {MIN_EVAL_POST} post years with ≥ {MIN_CLOSE_DAYS} "
                "close-overpass days, so the cleanest orbit-free comparison (A3 close) is "
                "insufficient everywhere."
            )
        L.append("")
    L += ["## Reason codes", ""]
    L += [f"- `{c}`: {t}" for c, t in out["reason_codes"].items()]
    L += ["", f"Districts: {out['district_inheritance']}.", ""]
    L += [
        "## Inputs",
        "",
        f"Code commit `{out['provenance']['code']['commit']}`.",
        "",
    ]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
