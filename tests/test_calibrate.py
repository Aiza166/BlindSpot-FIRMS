"""Tests for blindspot.calibrate. All numbers are hand-made fixtures, not FIRMS data."""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
import pytest

from blindspot import calibrate as cal
from conftest import make_detections


def _pdays(platform_dates: dict[str, list[str]]) -> pd.DataFrame:
    rows = [(p, pd.Timestamp(d)) for p, ds in platform_dates.items() for d in ds]
    return pd.DataFrame(rows, columns=["platform", "date"])


def _daily(rows):
    df = pd.DataFrame(rows, columns=["region", "platform", "date", "n"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_common_days_is_intersection():
    pd_ = _pdays({"Aqua": ["2012-01-10", "2012-01-25"], "SNPP": ["2012-01-25", "2012-01-26"]})
    assert list(cal.common_days(pd_, "Aqua", "SNPP")) == [pd.Timestamp("2012-01-25")]


def test_pair_totals_uses_common_days_only_and_zero_fills():
    pdays = _pdays(
        {
            "Aqua": ["2012-10-01", "2012-10-02", "2013-10-01"],
            "SNPP": ["2012-10-02", "2013-10-01"],  # S-NPP missing on 1 Oct 2012
        }
    )
    daily = _daily(
        [
            ("R", "Aqua", "2012-10-01", 100),  # not a common day: ignored
            ("R", "Aqua", "2012-10-02", 10),
            ("R", "SNPP", "2012-10-02", 30),
            ("R", "SNPP", "2013-10-01", 5),  # Aqua saw nothing in R that day -> a = 0
            ("Q", "Aqua", "2012-10-02", 1),
        ]
    )
    days = cal.common_days(pdays, "Aqua", "SNPP")
    p = cal.pair_totals(daily, days, "Aqua", "SNPP", [2012, 2013]).set_index(
        ["region", "year", "month"]
    )
    assert p.loc[("R", 2012, 10), ["a", "s", "n_days"]].tolist() == [10, 30, 1]
    assert p.loc[("R", 2013, 10), ["a", "s"]].tolist() == [0, 5]
    assert p.loc[("Q", 2013, 10), ["a", "s"]].tolist() == [0, 0]


def test_pair_totals_window_by_local_date():
    days = pd.DatetimeIndex(["2015-10-14", "2015-10-15", "2015-11-30", "2015-12-01"])
    daily = _daily([("R", "Aqua", d, 1) for d in days] + [("R", "SNPP", d, 2) for d in days])
    p = cal.pair_totals(daily, days, "Aqua", "SNPP", [2015], window=((10, 15), (11, 30)))
    assert p.a.sum() == 2 and p.s.sum() == 4
    assert set(p.month) == {10, 11}


def test_ratio_and_bootstrap_are_deterministic():
    a = np.array([10.0, 20.0, 30.0])
    s = np.array([20.0, 40.0, 60.0])
    assert cal.ratio_of_sums(a, s) == pytest.approx(2.0)
    assert np.isnan(cal.ratio_of_sums(np.zeros(3), s))
    b1 = cal.bootstrap_ratio(a, s, 50, np.random.default_rng(1))
    b2 = cal.bootstrap_ratio(a, s, 50, np.random.default_rng(1))
    assert np.array_equal(b1, b2)
    assert np.allclose(b1, 2.0)  # constant ratio -> every draw is 2


def test_fit_factors_ratio_of_totals_and_interval():
    pairs = pd.DataFrame(
        {
            "region": "R",
            "year": [2012, 2013, 2014, 2015],
            "month": 11,
            "a": [10.0, 10.0, 10.0, 10.0],
            "s": [20.0, 30.0, 25.0, 25.0],
            "n_days": 30,
        }
    )
    f = cal.fit_factors(pairs, b=500, seed=7).iloc[0]
    assert f.factor == pytest.approx(100 / 40)
    assert f.lo <= f.factor <= f.hi
    assert f.n_years == 4
    again = cal.fit_factors(pairs, b=500, seed=7).iloc[0]
    assert (f.lo, f.hi) == (again.lo, again.hi)


def test_era_source_follows_splice_rule():
    assert cal.era_source(2011, 12) == "Aqua"
    assert cal.era_source(2012, 1) == "SNPP"
    assert cal.era_source(2026, 10) == "SNPP"
    assert cal.era_source(2026, 11) == "NOAA20"


def _factors(region_month_f):
    return pd.DataFrame(
        [
            {"region": r, "month": m, "factor": f, "lo": f * 0.9, "hi": f * 1.1}
            for (r, m), f in region_month_f.items()
        ]
    )


def test_harmonize_one_source_per_month_never_sums_platforms():
    monthly = pd.DataFrame(
        [
            # Nov 2011: Aqua era. District D has detections in two calibration regions.
            ("ADM2", "D", "PK_Punjab", "Aqua", 2011, 11, 10),
            ("ADM2", "D", "rest_of_box", "Aqua", 2011, 11, 4),
            ("ADM2", "D", "PK_Punjab", "Terra", 2011, 11, 999),  # never used
            ("ADM2", "D", "PK_Punjab", "SNPP", 2011, 11, 999),  # S-NPP absent in 2011 anyway
            # Nov 2012: S-NPP observed; Aqua must not be added.
            ("ADM2", "D", "PK_Punjab", "SNPP", 2012, 11, 50),
            ("ADM2", "D", "PK_Punjab", "Aqua", 2012, 11, 999),
            # Nov 2026: after the S-NPP cut-over (2026-10) -> NOAA-20 x factor.
            ("ADM2", "D", "PK_Punjab", "NOAA20", 2026, 11, 8),
            ("ADM2", "D", "PK_Punjab", "SNPP", 2026, 11, 999),
        ],
        columns=["level", "shape_id", "calib_region", "platform", "year", "month", "n"],
    )
    shapes = pd.DataFrame({"level": ["ADM2", "ADM2"], "shape_id": ["D", "E"]})
    avail = pd.DataFrame(
        [
            ("Aqua", 2011, 11, 30),
            ("Aqua", 2012, 11, 30),
            ("SNPP", 2012, 11, 20),
            ("NOAA20", 2026, 11, 30),
            ("SNPP", 2026, 11, 30),
        ],
        columns=["platform", "year", "month", "days_available"],
    )
    fa = _factors({("PK_Punjab", 11): 3.0, ("rest_of_box", 11): 2.0})
    fn = _factors({("PK_Punjab", 11): 1.5})
    h = cal.harmonize(monthly, shapes, avail, fa, fn, first_month=(2011, 11)).set_index(
        ["shape_id", "year", "month"]
    )
    assert h.loc[("D", 2011, 11), "value"] == pytest.approx(10 * 3.0 + 4 * 2.0)
    assert h.loc[("D", 2011, 11), "source_platform"] == "Aqua"
    assert h.loc[("D", 2011, 11), "value_lo"] == pytest.approx(0.9 * 38)
    assert h.loc[("D", 2012, 11), "value"] == 50
    assert h.loc[("D", 2012, 11), "source_platform"] == "SNPP"
    assert bool(h.loc[("D", 2012, 11), "partial"])  # 20 of 30 days
    assert h.loc[("D", 2026, 11), "value"] == pytest.approx(8 * 1.5)
    assert h.loc[("D", 2026, 11), "source_platform"] == "NOAA20"
    assert h.loc[("E", 2012, 11), "value"] == 0  # zero-filled shape
    # Months whose source platform has no data at all are left out (2012-01..10 here).
    assert (h.index.get_level_values("year") == 2012).sum() == 2


def test_harmonize_undefined_factor_gives_null_not_zero():
    monthly = pd.DataFrame(
        [("CALIB", "R", "R", "Aqua", 2005, 7, 3)],
        columns=["level", "shape_id", "calib_region", "platform", "year", "month", "n"],
    )
    shapes = pd.DataFrame({"level": ["CALIB"], "shape_id": ["R"]})
    avail = pd.DataFrame(
        [("Aqua", 2005, 7, 31)], columns=["platform", "year", "month", "days_available"]
    )
    fa = pd.DataFrame([{"region": "R", "month": 7, "factor": np.nan, "lo": np.nan, "hi": np.nan}])
    h = cal.harmonize(monthly, shapes, avail, fa, fa.iloc[0:0], first_month=(2005, 7))
    assert np.isnan(h.value.iloc[0])


# ---------------------------------------------------------------- DuckDB builders


@pytest.fixture
def con():
    """Hand-made detections in one region R. 23:30 local on 31 Dec 2012 must land in 2012;
    00:30 local on 1 Jan 2013 must land in 2013, whatever the UTC date."""
    rows = [
        {"platform": "Aqua", "lat": 30.001, "lon": 74.001, "local": "2012-12-31 23:30"},
        {"platform": "Aqua", "lat": 30.002, "lon": 74.002, "local": "2012-12-31 13:30"},
        {"platform": "SNPP", "lat": 30.001, "lon": 74.001, "local": "2013-01-01 00:30"},
        {"platform": "SNPP", "lat": 30.30, "lon": 74.30, "local": "2012-12-31 13:30"},
    ]
    df = make_detections(rows)
    c = duckdb.connect()
    c.register("hotspots_masked", df)
    c.register("hotspots", df)
    pr = pd.DataFrame(
        {
            "lat": df.lat,
            "lon": df.lon,
            "level": "CALIB",
            "shape_iso": "",
            "shape_id": "R",
        }
    ).drop_duplicates()
    c.register("point_regions", pr)
    return c


def test_daily_counts_use_local_solar_date(con):
    d = cal.daily_calib_sql(con, grids=(0.05,))
    hot = d[d.unit == "hotspots"].set_index(["platform", "date"])["n"]
    assert hot[("Aqua", pd.Timestamp("2012-12-31"))] == 2
    assert hot[("SNPP", pd.Timestamp("2013-01-01"))] == 1
    cd = d[d.unit == "celldays_0.05"].set_index(["platform", "date"])["n"]
    assert cd[("Aqua", pd.Timestamp("2012-12-31"))] == 1  # two detections, one 0.05° cell


def test_saturation_share_both_over_either(con):
    days = pd.DatetimeIndex(["2012-12-31"])
    s = cal.saturation_sql(con, days, grids=(0.05,)).iloc[0]
    # 31 Dec: Aqua cell (600,1480) and S-NPP cell (606,1486) -> 2 either, 0 both
    assert (s.n_both, s.n_either) == (0, 2)
    s = cal.saturation_sql(con, days, grids=(1.0,)).iloc[0]
    assert (s.n_both, s.n_either) == (1, 1)
