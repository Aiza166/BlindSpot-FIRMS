"""T3 explanation-test logic on synthetic fixtures (D-039)."""

import math

import numpy as np
import pandas as pd
import pytest

from blindspot import t2, t3


def _p(rows):
    df = pd.DataFrame(rows, columns=["date", "a", "b", "ta", "tb"])
    df.index = pd.to_datetime(df.pop("date"))
    df["delta"] = df.ta - df.tb
    df["year"] = df.index.year
    return df


def test_close_days_strict_tolerance_and_both_seen():
    p = _p(
        [
            ("2015-10-20", 10, 40, 13.30, 13.25),  # 3 min -> usable
            ("2015-10-21", 10, 40, 13.50, 13.30),  # 12 min -> no
            ("2015-10-22", 0, 40, 13.30, 13.30),  # Aqua none -> no
            ("2015-10-23", 5, 10, 13.30 + 11 / 60, 13.30),  # 11 min -> no
        ]
    )
    q = t3.close_days(p)
    assert list(q.index.strftime("%m-%d")) == ["10-20"]


def _ns(day, night):
    return {
        str(y): {"day": d, "night": n, "share": n / (d + n), "n_days": 47}
        for y, d, n in zip(range(2012, 2026), day, night, strict=True)
    }


def test_a2_decline_vs_shift_signatures():
    rng = np.random.default_rng(0)
    pre = list(1000 * np.exp(rng.normal(0, 0.05, 10)))
    # D: day and night both fall
    d = t3.a2_viirs(_ns(pre + [300] * 4, [50] * 10 + [15] * 4), {})
    assert d["day_fall"] and d["night_fall"] and not d["night_share_rise"]
    # T: day falls, night rises
    t = t3.a2_viirs(_ns(pre + [500] * 4, [10, 11, 9, 10, 12, 10, 9, 11, 10, 10] + [40] * 4), {})
    assert t["day_fall"] and not t["night_fall"] and t["night_share_rise"]


def _a1(stable=True):
    return {"stable": stable, "theil_sen": {"slope_pct_per_year": 0.0}}


def _a2(day_fall, night_fall, rise):
    return {
        "day_fall": day_fall,
        "night_fall": night_fall,
        "night_share_rise": rise,
        "snpp_day_change_pct": -0.5,
        "snpp_night_change_pct": -0.5,
        "snpp_night_share_post_mean": 0.02,
        "snpp_night_share_pre_max": 0.01,
    }


def _a3(shift, direction, sufficient, sign):
    return (
        {"close_shift": shift, "post_vs_pre": direction},
        {"orbit_sufficient": sufficient, "residual_sign": sign, "post_residual_mean_pct": 0.1},
    )


def test_verdict_rules():
    c, k = _a3("inside", "higher", True, None)
    v = t3.verdicts(_a1(), _a2(False, False, False), c, k)
    assert (v["O"]["verdict"], v["T"]["verdict"], v["D"]["verdict"]) == (
        "supported",
        "not supported",
        "not supported",
    )
    c, k = _a3("outside", "higher", False, "positive")
    v = t3.verdicts(_a1(), _a2(True, False, True), c, k)
    assert (v["O"]["verdict"], v["T"]["verdict"], v["D"]["verdict"]) == (
        "not supported",
        "supported",
        "cannot separate",
    )
    c, k = _a3("insufficient", None, False, "positive")
    v = t3.verdicts(_a1(), _a2(True, True, True), c, k)
    assert v["O"]["verdict"] == "cannot separate"
    assert v["D"]["verdict"] == "supported"
    assert v["T"]["verdict"] == "cannot separate"  # night fell


def test_a3_curve_uses_pre_years_only_and_detects_residual():
    rng = np.random.default_rng(3)
    rows = []
    for y in range(2012, 2026):
        for k in range(20):
            dl = rng.normal(0, 0.3) + (1.0 if y >= 2022 else 0.0)
            ln = math.log(0.2) + 0.1 * dl + rng.normal(0, 0.05) + (0.5 if y >= 2022 else 0)
            rows.append((f"{y}-10-{1 + k:02d}", 100 * math.exp(ln), 100, 13.3 + dl, 13.3))
    p = _p(rows)
    k = t3.a3_curve(p, t2.yearly(p, None))
    assert k["slope_ln_per_hour"] == pytest.approx(0.1, abs=0.05)
    assert not k["orbit_sufficient"] and k["residual_sign"] == "positive"


def test_a4_step_normal_rule():
    g = pd.DataFrame(
        {"ratio": [4.0, 4.2, 3.8, 4.1, 3.9, 4.0, 4.3, 3.7, 4.0]}, index=range(2013, 2022)
    )
    g["ln_ratio"] = np.log(g.ratio)
    sd = g.ln_ratio.std(ddof=1)
    assert t3.a4_factor_spread(g, math.exp(sd) - 1)["step_normal"]
    assert not t3.a4_factor_spread(g, math.exp(3 * sd) - 1)["step_normal"]


def test_reliability_flags():
    a4, a5 = {"step_normal": False}, {"stable": True}
    f = t3.reliability(range(2010, 2026), {2022: 0.2, 2023: 0.6}, a4, a5, "not supported")
    assert f["2011"]["harmonization_reliable"] == "yes"
    assert f["2012"]["reasons"] == ["splice_step_outside_normal"]
    assert f["2022"]["harmonization_reliable"] == "yes"
    assert f["2023"]["reasons"] == ["aqua_overpass_drift"]
    assert f["2024"]["reasons"] == ["aqua_overpass_drift"]  # no delta -> caution
    f = t3.reliability(
        [2005, 2022], {2022: 0.1}, {"step_normal": True}, {"stable": False}, "supported"
    )
    assert f["2005"]["reasons"] == ["pre2012_terra_aqua_trend"]
    assert f["2022"]["reasons"] == ["burning_time_shift"]
