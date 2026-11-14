"""T2/T2b logic on synthetic fixtures (D-033)."""

import math

import numpy as np
import pandas as pd
import pytest

from blindspot import t2


def _daily(rows):
    df = pd.DataFrame(rows, columns=["region", "platform", "daynight", "date", "n", "t_med"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_matched_days_respect_tolerance_and_zero_days():
    d = _daily(
        [
            ("R", "Aqua", "D", "2015-10-20", 10, 13.6),
            ("R", "SNPP", "D", "2015-10-20", 40, 13.4),  # delta 0.2 h -> matched
            ("R", "Aqua", "D", "2015-10-21", 50, 14.5),
            ("R", "SNPP", "D", "2015-10-21", 50, 13.0),  # delta 1.5 h -> not matched
            ("R", "SNPP", "D", "2015-10-22", 30, 13.0),  # Aqua zero -> not matched
        ]
    )
    days = pd.DatetimeIndex(["2015-10-20", "2015-10-21", "2015-10-22"])
    p = t2.pair_days(t2.scene(d, "R", "Aqua"), t2.scene(d, "R", "SNPP"), days)
    gm = t2.yearly(p, 0.5)
    assert gm.loc[2015, "ratio"] == pytest.approx(10 / 40)
    assert gm.loc[2015, "n_days"] == 1
    ga = t2.yearly(p, None)
    assert ga.loc[2015, "ratio"] == pytest.approx(60 / 120)
    assert ga.loc[2015, "delta_h"] == pytest.approx(np.median([0.2, 1.5]))


def test_pi_mean_test_flags_shift_and_not_noise():
    rng = np.random.default_rng(1)
    base = pd.Series(rng.normal(0, 0.05, 10), index=range(2012, 2022))
    same = pd.concat([base, pd.Series([0.01, -0.02, 0.0, 0.03], index=range(2022, 2026))])
    shifted = pd.concat([base, pd.Series([0.5] * 4, index=range(2022, 2026))])
    assert not t2.pi_mean_test(same, range(2012, 2022), range(2022, 2026))["outside"]
    r = t2.pi_mean_test(shifted, range(2012, 2022), range(2022, 2026))
    assert r["outside"]
    m, s = base.mean(), base.std(ddof=1)
    half = r["t_quantile"] * s * math.sqrt(1 / 10 + 1 / 4)
    assert r["pi_ln"] == pytest.approx([m - half, m + half])


def test_theil_sen_detects_trend():
    yrs = range(2012, 2026)
    trend = pd.Series([0.1 * (y - 2012) for y in yrs], index=yrs)
    flat = pd.Series([0.0, 0.01] * 7, index=yrs)
    assert t2.theil_sen(trend, yrs)["excludes_zero"]
    assert t2.theil_sen(trend, yrs)["slope_ln_per_year"] == pytest.approx(0.1)
    assert not t2.theil_sen(flat, yrs)["excludes_zero"]


def test_drift_effect_recovers_slope():
    yrs = list(range(2012, 2026))
    delta = [0.0] * 10 + [0.2, 0.4, 0.6, 0.8]
    g = pd.DataFrame({"delta_h": delta, "ln_ratio": [0.7 * x for x in delta]}, index=yrs)
    e = t2.drift_effect(g, yrs, range(2012, 2022))
    assert e["slope_ln_per_hour"] == pytest.approx(0.7)
    assert e["effect_pct_per_hour"] == pytest.approx(math.exp(0.7) - 1)
    assert e["implied_effect_by_year"]["2025"] == pytest.approx(math.exp(0.7 * 0.8) - 1)


def test_mdd_formula():
    r = t2.mdd(0.1, 10, 4)
    assert r["ln"] == pytest.approx((1.959964 + 0.841621) * 0.1 * math.sqrt(0.35), rel=1e-5)


def test_night_share_and_overpass():
    d = _daily(
        [
            ("R", "SNPP", "D", "2020-11-01", 30, 13.5),
            ("R", "SNPP", "N", "2020-11-01", 10, 1.5),
            ("R", "SNPP", "D", "2020-11-02", 60, 13.0),
        ]
    )
    sc = t2.scene(d, "R", "SNPP")
    days = pd.DatetimeIndex(["2020-11-01", "2020-11-02", "2020-11-03"])
    ns = t2.night_share(sc, days)["2020"]
    assert ns["share"] == pytest.approx(10 / 100)
    assert ns["n_days"] == 3
    assert t2.overpass_by_year(sc, days)["2020"]["median_h"] == pytest.approx(13.25)


def test_reevaluate_t1_conditional():
    t1 = {"verdict_primary": {"A": {"step_pass": True, "heldout_pass": False}}}
    r = t2.reevaluate_t1(t1, {"A": {"label": "drift"}})["A"]
    assert r["pass"] and r["heldout"].startswith("not judged")
    r = t2.reevaluate_t1(t1, {"A": {"label": "inconclusive"}})["A"]
    assert r["pass"] and "2012 step only" in r["label"]
    r = t2.reevaluate_t1(t1, {"A": {"label": "no drift"}})["A"]
    assert not r["pass"]


def _g(n_days, delta):
    ys = list(range(2012, 2026))
    gm = pd.DataFrame({"n_days": n_days, "ln_ratio": [0.0] * 14}, index=ys)
    ga = pd.DataFrame({"delta_h": delta}, index=ys)
    return gm, ga


def test_evaluable_years_and_inconclusive():
    gm, ga = _g([20] * 10 + [25, 15, 12, 3], [0.1] * 10 + [0.25, 0.52, 0.84, 1.46])
    ev = t2.evaluable_years(gm, ga, t2.TEST_YEARS)
    assert [ev[str(y)]["evaluable"] for y in t2.TEST_YEARS] == [True, False, False, False]
    assert t2.revised_verdict(gm, ev)["label"] == "inconclusive"
    gm, ga = _g([20] * 14, [0.1] * 14)
    gm["ln_ratio"] = np.r_[np.random.default_rng(0).normal(0, 0.05, 10), [0.0] * 4]
    v = t2.revised_verdict(gm, t2.evaluable_years(gm, ga, t2.TEST_YEARS))
    assert v["label"] == "no drift"


def test_delta_bins_split_by_era():
    idx = pd.to_datetime(["2015-10-20", "2015-10-21", "2024-10-20"])
    p = pd.DataFrame({"a": [1.0, 2, 3], "b": [10.0, 10, 10], "delta": [0.1, 0.2, 1.2]}, index=idx)
    p["year"] = p.index.year
    b = t2.delta_bins(p)
    pre = [x for x in b if x["era"] == "2012-2021"]
    assert len(pre) == 1 and pre[0]["ratio"] == pytest.approx(0.15) and pre[0]["n_days"] == 2
    assert len(t2.day_points(p)) == 3


def test_pitch_fill_replaces_only_marked_block():
    from blindspot import pitch

    plan = f"a\n{pitch.START}\nold\n{pitch.END}\nb"
    assert pitch.fill(plan, "new") == f"a\n{pitch.START}\nnew\n{pitch.END}\nb"
    with pytest.raises(ValueError):
        pitch.fill("no markers", "x")


def test_pitch_word_limit_and_clause_gate():
    from blindspot import pitch

    def bins(pre, post):
        return [
            {"bin_lo_h": 0.0, "bin_hi_h": 0.5, "era": "2012-2021", "n_days": 10, "ratio": pre},
            {"bin_lo_h": 0.0, "bin_hi_h": 0.5, "era": "2022-2025", "n_days": 10, "ratio": post},
        ]

    ns = {str(y): {"share": 0.001 if y < 2022 else 0.02} for y in range(2012, 2026)}
    step = {"step_2012": {"raw_step": 6.0}}
    t1 = {"results": {"hotspots": {pitch.PK: step, pitch.IN: step}}}
    t2_ = {
        "t1_reevaluated": {pitch.PK: {"step_pass": True}, pitch.IN: {"step_pass": True}},
        "t2b": {pitch.IN: {"night_share": {"SNPP": ns}}},
        "t2": {
            pitch.IN: {"delta_bins": bins(0.2, 0.3)},
            pitch.CTRL: {"all_common_days": {"pi_test": {"outside": False}}},
        },
    }
    # D-034 evidence alone no longer allows the clause; only T3 (D-039) does.
    s = pitch.sentence(t1, t2_).split("\n")[0].removeprefix("> ")
    assert "stops being comparable" in s and "+600%" in s and "afternoon" not in s

    def t3(tv, dv):
        ev = {"T": {"verdict": tv}, "D": {"verdict": dv}, "O": {"verdict": "x"}}
        return {"t3": {pitch.IN: {"evidence": ev}}}

    s = pitch.sentence(t1, t2_, t3("supported", "cannot separate")).split("\n")[0]
    assert "moved past afternoon" in s
    s = pitch.sentence(t1, t2_, t3("cannot separate", "supported"))
    assert "afternoon" not in s and "stops being comparable" in s


def test_delta_bins_open_ends_are_null_and_json_strict():
    """Open-ended bins are written as null, never Infinity (CODE_REVIEW #5, D-038)."""
    import json

    idx = pd.to_datetime(["2015-10-20", "2015-10-21", "2024-10-20"])
    p = pd.DataFrame({"a": [1.0, 2, 3], "b": [10.0, 10, 10], "delta": [-3.0, 0.2, 4.0]}, index=idx)
    p["year"] = p.index.year
    b = t2.delta_bins(p)
    lo = [x for x in b if x["bin_hi_h"] == -0.5]
    hi = [x for x in b if x["bin_lo_h"] == 1.5]
    assert lo[0]["bin_lo_h"] is None and hi[0]["bin_hi_h"] is None
    json.dumps(b, allow_nan=False)


def test_report_and_pitch_accept_null_bin_edges():
    from blindspot import report_t2

    assert report_t2._bin_label(None, -0.5) == "(−∞, -0.5]"
    assert report_t2._bin_label(1.5, None) == "(1.5, ∞)"
