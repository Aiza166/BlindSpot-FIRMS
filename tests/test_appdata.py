"""Tests for blindspot.appdata. All numbers are hand-made fixtures, not FIRMS data."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from blindspot import appdata as ad

PLATFORMS = ("Terra", "Aqua", "SNPP", "NOAA20")


def _months(first=(2003, 1), last=(2004, 12)):
    out, (y, m) = [], first
    while (y, m) <= last:
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _harm(shape_id="D1", last=(2004, 12), partial_at=()):
    rows = []
    for i, (y, m) in enumerate(_months(last=last)):
        rows.append(
            {
                "level": "ADM2",
                "shape_id": shape_id,
                "year": y,
                "month": m,
                "source_platform": "Aqua",
                "value": float(i) + 0.123,
                "value_lo": float(i),
                "value_hi": float(i) + 1.0,
                "partial": (y, m) in partial_at,
            }
        )
    return pd.DataFrame(rows)


def _raw(shape_id="D1", last=(2004, 12)):
    rows = []
    for y, m in _months(last=last):
        for p, n in (("Terra", 3), ("Aqua", 5)):
            rows.append(
                {
                    "level": "ADM2",
                    "shape_id": shape_id,
                    "platform": p,
                    "year": y,
                    "month": m,
                    "n": n,
                    "partial": False,
                }
            )
    return pd.DataFrame(rows)


def _meta():
    return {
        "id": "D1",
        "level": "ADM2",
        "name": "Fixture district",
        "country": "PAK",
        "adm1": {"id": "A1", "name": "Fixture province"},
        "bbox": [70.0, 30.0, 71.0, 31.0],
    }


def _doc(**kw):
    return ad.area_doc(_meta(), _harm(**kw), _raw(), last_month=(2004, 12), provenance={"x": 1})


def test_monthly_median_by_calendar_month_skips_partial_and_out_of_baseline():
    df = pd.DataFrame(
        {
            "year": [2003, 2004, 2005, 2006, 2003, 2004],
            "month": [1, 1, 1, 1, 2, 2],
            "value": [1.0, 3.0, 100.0, 7.0, 4.0, 6.0],
            "partial": [False, False, False, True, False, False],
        }
    )
    med = ad.monthly_median(df, years=(2003, 2005))
    assert med["values"][0] == 3.0  # median of 1, 3, 100 (2006 out of baseline, partial)
    assert med["values"][1] == 5.0
    assert med["values"][2] is None
    assert med["n_years"][:3] == [3, 2, 0]
    assert med["baseline_years"] == [2003, 2005]


def test_area_doc_schema_valid():
    doc = _doc()
    ad.validate_area_doc(doc)
    assert doc["period"] == {"first": "2003-01", "last": "2004-12", "n_months": 24}
    assert len(doc["harmonized"]["value"]) == 24
    assert doc["harmonized"]["value"][0] == 0.1  # rounded to 1 decimal
    assert set(doc["raw"]) == set(PLATFORMS)
    assert doc["raw"]["SNPP"]["n"] == [None] * 24
    assert [e["label"] for e in doc["eras"]][0] == "MODIS-scaled"
    assert doc["units"]["harmonized"] == "S-NPP-equivalent hotspots"
    assert "commit" in json.dumps(doc["provenance"]) or doc["provenance"] == {"x": 1}


def test_validate_rejects_missing_key():
    doc = _doc()
    del doc["median"]
    with pytest.raises(ValueError):
        ad.validate_area_doc(doc)


def test_no_platform_sums_anywhere():
    doc = _doc()
    # Each platform keeps its own counts; no key holds a cross-platform total.
    assert doc["raw"]["Terra"]["n"][0] == 3
    assert doc["raw"]["Aqua"]["n"][0] == 5
    flat = json.dumps(doc)
    assert 8 not in doc["raw"]["Terra"]["n"] + doc["raw"]["Aqua"]["n"]
    for bad in ("total", "sum", "all_platforms", "combined"):
        assert f'"{bad}"' not in flat
    ad.validate_area_doc(doc)
    doc["raw"]["total"] = {"n": [8] * 24}
    with pytest.raises(ValueError):
        ad.validate_area_doc(doc)


def test_partial_months_flagged_and_trailing_trimmed():
    harm = _harm(last=(2005, 1), partial_at={(2005, 1)})
    assert ad.last_complete_month(harm) == (2004, 12)
    doc = ad.area_doc(
        _meta(), _harm(partial_at={(2003, 2)}), _raw(), last_month=(2004, 12), provenance={}
    )
    assert doc["harmonized"]["partial"][1] is True


def test_csv_cap_constant():
    assert ad.CSV_ROW_CAP == 200_000
    c = ad.constants()
    assert c["csv_row_cap"] == 200_000
    assert c["tile_deg"] == 1


def test_tile_key_floors_and_clamps_box_edge():
    assert ad.tile_key(30.99, 74.01) == (30, 74)
    assert ad.tile_key(37.0, 80.0) == (36, 79)
    assert ad.tile_key(23.0, 60.0) == (23, 60)


def test_attribution_names_odbl_for_ind_adm2():
    text = ad.attribution_markdown()
    assert "ODbL 1.0" in text
    assert "IND ADM2" in text
    assert "10.5067/FIRMS/MODIS/MCD14ML" in text
    lic = ad.licenses()
    ind2 = [x for x in lic if x["dataset"] == "geoBoundaries IND ADM2"][0]
    assert "ODbL" in ind2["licence"]
    assert ind2["applies_to"]


def test_constants_export_partial_coverage_from_calibrate():
    """The web reads the complete-month rule from constants.json (rule 7, D-038)."""
    from blindspot.calibrate import PARTIAL_COVERAGE

    assert ad.constants()["partial_coverage"] == PARTIAL_COVERAGE


def test_tiles_carry_exact_adm2_id():
    """District CSV filters by the exact ADM2 shape_id, not the simplified polygon (D-038)."""
    assert "adm2_id" in ad.TILE_COLUMNS


def test_tile_adm2_ids_join_point_regions(tmp_path):
    import duckdb

    pr = tmp_path / "point_regions.parquet"
    pd.DataFrame(
        {
            "lat": [30.1, 30.1, 31.0],
            "lon": [74.1, 74.1, 75.0],
            "level": ["ADM1", "ADM2", "ADM1"],
            "shape_iso": ["PAK"] * 3,
            "shape_id": ["P1", "D9", "P1"],
        }
    ).to_parquet(pr)
    con = duckdb.connect()
    con.execute("CREATE VIEW h AS SELECT * FROM (VALUES (30.1, 74.1), (31.0, 75.0)) t(lat, lon)")
    df = con.execute(ad.ADM2_JOIN_SQL.format(src="h"), [str(pr)]).df().sort_values("lat")
    assert df.adm2_id.tolist()[0] == "D9"
    assert pd.isna(df.adm2_id.tolist()[1])


def test_noaa20_era_flagged_not_held_out_validated():
    """NOAA-20 factor is fit on 2019-2025, overlapping the held-out years (D-038)."""
    e = [x for x in ad.eras((2025, 12)) if x["source"] == "NOAA20"][0]
    assert e["note"] == "NOAA-20 factor not held-out validated"


def _t3():
    rel = {"2011": {"harmonization_reliable": "yes", "reasons": []}}
    rel["2024"] = {"harmonization_reliable": "caution", "reasons": ["aqua_overpass_drift"]}
    return {
        "reason_codes": {"aqua_overpass_drift": "drift"},
        "t3": {r: {"reliability": rel} for r in ("PK_Punjab", "IN_Punjab", "rest_of_box")},
    }


def test_reliability_region_and_district_inheritance():
    rmeta = {
        "PK_Punjab": {"adm1": {"id": "PK1"}},
        "IN_Punjab": {"adm1": {"id": "IN1"}},
        "rest_of_box": {"adm1": None},
    }
    assert ad.calib_region_of({"adm1": {"id": "IN1"}}, rmeta) == "IN_Punjab"
    assert ad.calib_region_of({"adm1": {"id": "XX"}}, rmeta) == "rest_of_box"
    r = ad.reliability_doc(_t3(), "IN_Punjab", inherited=True)
    assert r["calib_region"] == "IN_Punjab" and r["inherited"] is True
    assert r["caution_years"] == {"2024": ["aqua_overpass_drift"]}
    assert r["reason_codes"]["aqua_overpass_drift"] == "drift"


def test_nrt_mask_doc_lists_integer_cells(tmp_path):
    import json as _json

    import pyarrow as _pa
    import pyarrow.parquet as _pq

    from blindspot.appdata import nrt_mask_doc

    report = {"parameters": {"rule": "year-round", "grid_deg": 0.01}}
    (tmp_path / "mask_report.json").write_text(_json.dumps(report))
    _pq.write_table(
        _pa.table({"cell_lat": [3100, 2301], "cell_lon": [7400, 7010], "n_years": [3, 4]}),
        tmp_path / "persistent_mask_cells.parquet",
    )
    doc = nrt_mask_doc(tmp_path)
    assert doc["grid_deg"] == 0.01
    assert doc["cells"] == [[2301, 7010], [3100, 7400]]


# ------------------------------------------------------------ D-042 critical periods


def _seasonal(profile: dict[int, float], years=range(2003, 2011), flagged=None, flag_mult=10.0):
    rows = []
    for y in years:
        for m in range(1, 13):
            v = profile.get(m, 1.0) * (flag_mult if flagged and y in flagged else 1.0)
            rows.append({"year": y, "month": m, "value": v, "partial": False})
    return pd.DataFrame(rows)


def test_critical_months_top_quartile_onset_peak_end():
    df = _seasonal({10: 50.0, 11: 90.0, 12: 40.0})
    med, crit = ad.critical_periods(df, [], (2010, 12))
    assert crit["months"] == [10, 11, 12]  # 3 of 12 are at or above the 75th percentile
    assert (crit["onset"], crit["peak"], crit["end"]) == (10, 11, 12)
    assert crit["resolution"] == "month" and crit["other_months"] == []
    assert med["excluded_years"] == []


def test_critical_run_wraps_over_december_and_lists_other_months():
    df = _seasonal({12: 80.0, 1: 70.0, 5: 60.0})
    _, crit = ad.critical_periods(df, [], (2010, 12))
    assert (crit["onset"], crit["peak"], crit["end"]) == (12, 12, 1)
    assert crit["other_months"] == [5]


def test_caution_years_left_out_of_typical_and_critical():
    df = _seasonal({11: 90.0, 4: 5.0}, flagged={2009, 2010}, flag_mult=0.0)
    allv, _ = ad.critical_periods(df, [], (2010, 12))
    ex, crit = ad.critical_periods(df, [2009, 2010], (2010, 12))
    assert allv["values"][10] == 90.0 and ex["values"][10] == 90.0
    assert ex["excluded_years"] == [2009, 2010] and ex["n_years"][10] == 6
    assert crit["excluded_years"] == [2009, 2010]
    # flagged years inflated 10x: the all-years median moves, the excluding one does not
    df2 = _seasonal({11: 90.0}, years=range(2003, 2011), flagged={2008, 2009, 2010, 2007})
    a, _ = ad.critical_periods(df2, [], (2010, 12))
    e, _ = ad.critical_periods(df2, [2007, 2008, 2009, 2010], (2010, 12))
    assert a["values"][10] == 495.0 and e["values"][10] == 90.0


def test_months_with_too_few_years_do_not_take_part():
    df = _seasonal({11: 90.0}, years=range(2003, 2007))  # 4 years < MIN_YEARS_CRITICAL
    _, crit = ad.critical_periods(df, [], (2006, 12))
    assert crit["months"] == [] and crit["peak"] is None and crit["threshold"] is None


def test_this_year_vs_typical_uses_latest_complete_month():
    df = _seasonal({11: 90.0, 12: 40.0})
    df.loc[(df.year == 2010) & (df.month == 12), "value"] = 80.0
    _, crit = ad.critical_periods(df, [2010], (2010, 12))
    t = crit["this_year"]
    assert t["month"] == "2010-12" and t["value"] == 80.0 and t["typical"] == 40.0
    assert t["ratio"] == 2.0 and t["year_flagged"] is True and t["in_critical"] is True


def test_area_doc_carries_critical_and_median_excl_flagged():
    doc = _doc()
    assert "critical" in doc and "median_excl_flagged" in doc
    assert doc["median"]["harmonized"]["values"] == doc["median_excl_flagged"]["values"]
    doc2 = ad.area_doc(
        _meta(), _harm(), _raw(), last_month=(2004, 12), provenance={}, caution_years=[2004]
    )
    assert doc2["median_excl_flagged"]["excluded_years"] == [2004]
