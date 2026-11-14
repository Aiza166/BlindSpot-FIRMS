"""Tests for blindspot.t1. Synthetic pairs only; the numbers are not FIRMS data."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from blindspot import t1


def _pairs(ratio_by_year: dict[int, float], a: float = 100.0) -> pd.DataFrame:
    """Oct and Nov rows, Aqua total `a` in each month, S-NPP = ratio * a."""
    rows = []
    for y, r in ratio_by_year.items():
        for m in (10, 11):
            rows.append({"region": "R", "year": y, "month": m, "a": a, "s": r * a, "n_days": 20})
    return pd.DataFrame(rows)


def test_month_factors_ratio_of_totals():
    p = _pairs({2013: 2.0, 2014: 4.0})
    f = t1.month_factors(p, [2013, 2014])
    assert f == {10: pytest.approx(3.0), 11: pytest.approx(3.0)}


def test_step_test_uses_factors_without_2012():
    # 2012 ratio 3.0; 2013-2021 ratio 3.0 -> harmonized step 0, raw step +200%.
    ratios = {y: 3.0 for y in range(2012, 2022)}
    p = _pairs(ratios)
    res = t1.step_test(p, p, step_year=2012, fit_years=range(2013, 2022), b=200, seed=1)
    assert res["raw_step"] == pytest.approx(2.0)
    assert res["harmonized_step"] == pytest.approx(0.0, abs=1e-12)
    assert res["ratio"] == pytest.approx(0.0, abs=1e-12)
    assert res["pass"] is True

    # 2012 itself is unusual (ratio 4) while the fit years say 3: the step is not hidden.
    ratios[2012] = 4.0
    p = _pairs(ratios)
    res = t1.step_test(p, p, step_year=2012, fit_years=range(2013, 2022), b=200, seed=1)
    assert res["raw_step"] == pytest.approx(3.0)
    assert res["harmonized_step"] == pytest.approx(4 / 3 - 1)
    assert res["ratio"] == pytest.approx((1 / 3) / 3.0)
    assert res["pass"] is False
    assert res["ratio_ci95"][0] <= res["ratio"] <= res["ratio_ci95"][1]


def test_heldout_prediction_interval_formula():
    rng = np.random.default_rng(0)
    calib = {y: float(np.exp(rng.normal(np.log(3.0), 0.1))) for y in range(2012, 2022)}
    held = {2022: 3.0, 2023: 3.0, 2024: 30.0, 2025: 3.0}
    p = _pairs({**calib, **held})
    res = t1.heldout_test(p, p, calib_years=range(2012, 2022), heldout_years=range(2022, 2026))
    # Recompute the interval by hand from leave-one-year-out residuals.
    e = []
    for y in range(2012, 2022):
        others = [v for k, v in calib.items() if k != y]
        f = sum(others) / len(others)  # equal Aqua totals -> ratio of sums = mean ratio
        e.append(math.log(calib[y] / f))
    e = np.array(e)
    half = stats.t.ppf(0.975, 9) * e.std(ddof=1) * math.sqrt(1 + 1 / 10)
    assert res["pi_log"] == pytest.approx([e.mean() - half, e.mean() + half])
    by_year = {r["year"]: r for r in res["years"]}
    assert by_year[2022]["inside"] is True
    assert by_year[2024]["inside"] is False
    assert res["n_inside"] == 3 and res["n"] == 4
    assert res["pass"] is False
    lo, hi = by_year[2022]["observed_pi95"]
    assert lo < by_year[2022]["observed"] < hi


def test_verdict_is_provisional_pending_t2():
    v = t1.verdict({"pass": True}, {"pass": True})
    assert v["pass"] is True
    assert v["status"] == "provisional pending T2"
    assert t1.verdict({"pass": False}, {"pass": True})["pass"] is False
