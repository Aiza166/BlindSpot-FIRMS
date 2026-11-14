"""Tests for blindspot.extend: appending 2026 to the app's area documents (decisions.md W-12)."""

from __future__ import annotations

import copy

import pandas as pd
import pytest

from blindspot import appdata, extend

PLATFORMS = appdata.PLATFORMS


def _doc(last=(2025, 12)) -> dict:
    """Small but valid area document, 2024-01 to `last`, values = month number."""
    months = appdata.month_range((2024, 1), last)
    n = len(months)
    harm = pd.DataFrame(
        {
            "year": [y for y, _ in months],
            "month": [m for _, m in months],
            "value": [float(m) for _, m in months],
            "value_lo": [float(m) for _, m in months],
            "value_hi": [float(m) for _, m in months],
            "source_platform": ["SNPP"] * n,
            "partial": [False] * n,
        }
    )
    raw = pd.concat(
        [
            pd.DataFrame(
                {
                    "platform": p,
                    "year": harm.year,
                    "month": harm.month,
                    "n": harm.month.astype(int),
                    "partial": False,
                }
            )
            for p in PLATFORMS
        ],
        ignore_index=True,
    )
    meta = {
        "id": "X",
        "level": "ADM2",
        "name": "X",
        "country": "PAK",
        "adm1": {"id": "A", "name": "Punjab"},
        "bbox": [70, 30, 71, 31],
    }
    doc = appdata.area_doc(meta, harm, raw, last, {"commit": "abc"}, first_month=(2024, 1))
    doc["reliability"] = {
        "source": "results/t3.json (D-039)",
        "calib_region": "PK_Punjab",
        "inherited": True,
        "years": ["2024", "2025"],
        "caution_years": {"2025": ["aqua_overpass_drift"]},
        "reason_codes": {"aqua_overpass_drift": "drift"},
    }
    return doc


def _new(months: list[tuple[int, int]], source="SNPP", value=100.0):
    harm = pd.DataFrame(
        {
            "year": [y for y, _ in months],
            "month": [m for _, m in months],
            "value": value,
            "value_lo": value,
            "value_hi": value,
            "source_platform": source,
            "partial": False,
        }
    )
    raw = pd.concat(
        [
            pd.DataFrame(
                {"platform": p, "year": harm.year, "month": harm.month, "n": 7, "partial": False}
            )
            for p in PLATFORMS
        ],
        ignore_index=True,
    )
    return harm, raw


PROV = {"SNPP": "2026-08", "NOAA20": "2026-08", "Aqua": "2026-09", "Terra": "2026-09"}


def test_appends_months_and_keeps_history():
    doc = _doc()
    before = copy.deepcopy(doc)
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 10)))
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {"note": "x"}, first_year=2024)
    n_old = before["period"]["n_months"]
    assert out["period"] == {"first": "2024-01", "last": "2026-10", "n_months": n_old + 10}
    assert out["harmonized"]["value"][:n_old] == before["harmonized"]["value"]
    assert out["harmonized"]["value"][n_old:] == [100.0] * 10
    for p in PLATFORMS:
        assert out["raw"][p]["n"][:n_old] == before["raw"][p]["n"]
        assert out["raw"][p]["n"][n_old:] == [7] * 10
    appdata.validate_area_doc(out)


def test_medians_do_not_move():
    doc = _doc()
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 10)), value=1e6)
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {}, first_year=2024)
    assert out["median"] == doc["median"]
    assert out["median_excl_flagged"]["values"] == doc["median_excl_flagged"]["values"]


def test_provisional_flags_follow_each_platform():
    doc = _doc()
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 10)))
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {}, first_year=2024)
    n_old = doc["period"]["n_months"]
    hp = out["harmonized"]["provisional"]
    assert hp[:n_old] == [False] * n_old
    # Jan-Jul standard, Aug-Oct near-real-time for S-NPP (the harmonized source)
    assert hp[n_old:] == [False] * 7 + [True] * 3
    assert out["raw"]["Aqua"]["provisional"][n_old:] == [False] * 8 + [True] * 2
    assert out["raw"]["NOAA20"]["provisional"][n_old:] == [False] * 7 + [True] * 3


def test_2026_is_flagged_as_not_tested():
    doc = _doc()
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 10)))
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {}, first_year=2024)
    rel = out["reliability"]
    assert rel["years"][-1] == "2026"
    assert rel["caution_years"]["2026"] == ["not_tested"]
    assert "not_tested" in rel["reason_codes"]
    assert rel["caution_years"]["2025"] == ["aqua_overpass_drift"]  # history kept


def test_this_year_line_moves_to_the_new_last_month():
    doc = _doc()
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 10)))
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {}, first_year=2024)
    ty = out["critical"]["this_year"]
    assert ty["month"] == "2026-10" and ty["value"] == 100.0 and ty["year_flagged"] is True


def test_refuses_a_gap_or_an_overlap():
    harm, raw = _new(appdata.month_range((2026, 2), (2026, 10)))
    with pytest.raises(ValueError, match="contiguous"):
        extend.extend_doc(_doc(), harm, raw, (2026, 10), PROV, {}, first_year=2024)
    harm, raw = _new(appdata.month_range((2025, 12), (2026, 10)))
    with pytest.raises(ValueError, match="contiguous"):
        extend.extend_doc(_doc(), harm, raw, (2026, 10), PROV, {}, first_year=2024)


def test_missing_months_become_none_not_zero():
    doc = _doc()
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 9)))  # no October row
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {}, first_year=2024)
    assert out["harmonized"]["value"][-1] is None
    assert out["raw"]["SNPP"]["n"][-1] is None


def test_frozen_mask_drops_masked_cells_only():
    df = pd.DataFrame({"lat": [30.005, 30.015], "lon": [70.005, 70.005]})
    cells = {(3000, 7000)}
    kept = extend.apply_frozen_mask(df, cells, 0.01)
    assert kept.lat.tolist() == [30.015]


def test_filter_rows_uses_type_only_for_standard_data():
    base = {
        "in_box": True,
        "passes_conf": True,
        "platform": "SNPP",
        "acq_datetime_utc": pd.Timestamp("2026-08-01T08:00Z"),
        "lat": 30.0,
        "lon": 70.0,
        "local_solar_datetime": pd.Timestamp("2026-08-01T12:40"),
    }
    df = pd.DataFrame(
        [
            {**base, "passes_standard": True, "passes_type": True},
            {**base, "lat": 30.1, "passes_standard": True, "passes_type": False},
            {**base, "lat": 30.2, "passes_standard": False, "passes_type": False},  # NRT: no type
            {**base, "lat": 30.2, "passes_standard": False, "passes_type": False},  # duplicate
        ]
    )
    out = extend.filter_rows(df, 2026, (2026, 10))
    assert sorted(out.lat.tolist()) == [30.0, 30.2]


def test_stored_baseline_is_kept_not_recomputed_from_rounded_values():
    """The stored 2003-2025 median and critical period came from full-precision series in the
    pipeline; the app document holds rounded values. Recomputing from those can move the last
    digit, so the extension must keep the stored baseline and only move the "this year" line."""
    doc = _doc()
    doc["median_excl_flagged"]["values"][9] = 10.04  # not what the rounded doc values give
    doc["critical"]["threshold"] = 9.87
    before = copy.deepcopy(doc)
    harm, raw = _new(appdata.month_range((2026, 1), (2026, 10)))
    out = extend.extend_doc(doc, harm, raw, (2026, 10), PROV, {}, first_year=2024)
    assert out["median_excl_flagged"] == before["median_excl_flagged"]
    crit = {k: v for k, v in out["critical"].items() if k != "this_year"}
    assert crit == {k: v for k, v in before["critical"].items() if k != "this_year"}
    ty = out["critical"]["this_year"]
    assert ty["month"] == "2026-10"
    assert ty["typical"] == 10.04
    assert ty["ratio"] == appdata._r(100.0 / 10.04, 3)
    assert ty["in_critical"] is (10 in before["critical"]["months"])
