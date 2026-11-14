"""Tests for blindspot.mask. All detections are hand-written (see conftest.py).

The first block tests the old D-022 rule (`rule="seasonal-offseason"`, kept for the comparison
report); the second block tests the default D-024 year-round rule.
"""

from __future__ import annotations

import json

import duckdb
import pytest

from blindspot import mask
from conftest import make_detections

OLD = "seasonal-offseason"

# Cell A: active in Jan 2013, Aug 2014 and Mar 2016 -> 3 distinct off-season years -> masked.
# Cell B: active in 2013, 2014, 2016 but only in Nov (crop season) -> not masked.
# Cell C: active in Feb 2013 and Feb 2014 only (2 years) -> not masked.
# Cell D: many detections, all in one year (Jul 2015) -> not masked.
A = (30.0012, 74.0012)
B = (30.5012, 74.5012)
C = (31.0012, 75.0012)
D = (31.5012, 75.5012)


def _rows():
    rows = []
    for local in ("2013-01-10 13:00", "2014-08-05 13:00", "2016-03-01 13:00"):
        rows.append({"platform": "SNPP", "lat": A[0], "lon": A[1], "local": local})
    # A also burns in crop season: these rows are removed by the mask too.
    rows.append({"platform": "Aqua", "lat": A[0], "lon": A[1], "local": "2016-11-01 13:30"})
    for local in ("2013-11-01 13:00", "2014-11-02 13:00", "2016-11-03 13:00"):
        rows.append({"platform": "SNPP", "lat": B[0], "lon": B[1], "local": local})
    for local in ("2013-02-01 13:00", "2014-02-01 13:00"):
        rows.append({"platform": "Aqua", "lat": C[0], "lon": C[1], "local": local})
    for day in range(1, 6):
        rows.append(
            {"platform": "Aqua", "lat": D[0], "lon": D[1], "local": f"2015-07-0{day} 13:00"}
        )
    return rows


@pytest.fixture
def con():
    c = duckdb.connect()
    df = make_detections(_rows())  # noqa: F841  (registered below)
    c.register("hotspots_filtered", df)
    return c


def test_cell_index_is_floor_of_coordinate_over_grid():
    assert mask.cell_index(30.0012, 0.01) == 3000
    assert mask.cell_index(-0.0001, 0.01) == -1
    assert mask.cell_index(31.5, 0.01) == 3150  # 31.5/0.01 is 3149.999... in floating point


def test_persistent_cell_found(con):
    result = mask.build_mask(con, grid_deg=0.01, rule=OLD)
    cells = result.cells
    assert len(cells) == 1
    row = cells.iloc[0]
    assert (row["cell_lat"], row["cell_lon"]) == (3000, 7400)
    assert row["n_years"] == 3
    assert list(row["years"]) == [2013, 2014, 2016]


def test_min_years_is_configurable(con):
    result = mask.build_mask(con, grid_deg=0.01, min_years=2, rule=OLD)
    got = {(r.cell_lat, r.cell_lon) for r in result.cells.itertuples()}
    assert got == {(3000, 7400), (3100, 7500)}


def test_months_are_configurable(con):
    result = mask.build_mask(con, grid_deg=0.01, months=(11,), rule=OLD)
    got = {(r.cell_lat, r.cell_lon) for r in result.cells.itertuples()}
    assert got == {(3050, 7450)}


def test_share_removed_is_per_platform(con):
    result = mask.build_mask(con, grid_deg=0.01, rule=OLD)
    # SNPP: 6 detections, 3 in cell A. Aqua: 8 detections, 1 in cell A.
    assert result.removed == {"Aqua": 1, "SNPP": 3}
    assert result.total == {"Aqua": 8, "SNPP": 6}
    assert result.share_removed == {"Aqua": pytest.approx(1 / 8), "SNPP": pytest.approx(0.5)}


def test_grid_size_changes_cells(con):
    # On a 1-degree grid C (2 years) and D (1 year) share cell (31, 75), which then has 3 years.
    result = mask.build_mask(con, grid_deg=1.0, min_years=3, rule=OLD)
    got = {(r.cell_lat, r.cell_lon) for r in result.cells.itertuples()}
    # Cell (31, 75) holds C (2013, 2014) and D (2015) -> 3 years.
    assert (31, 75) in got


def test_apply_mask_flags_rows(con):
    result = mask.build_mask(con, grid_deg=0.01, rule=OLD)
    mask.apply_mask(con, result, source_view="hotspots_filtered")
    flagged = con.execute(
        "SELECT count(*) FROM hotspots_masked_flags WHERE in_persistent_mask"
    ).fetchone()[0]
    kept = con.execute("SELECT count(*) FROM hotspots_masked").fetchone()[0]
    assert flagged == 4
    assert kept == 14 - 4


def test_invalid_arguments(con):
    with pytest.raises(ValueError):
        mask.build_mask(con, grid_deg=0)
    with pytest.raises(ValueError):
        mask.build_mask(con, months=(13,))
    with pytest.raises(ValueError):
        mask.build_mask(con, source_view="hotspots; DROP TABLE x")
    with pytest.raises(ValueError):
        mask.build_mask(con, rule="nonsense")
    with pytest.raises(ValueError):
        mask.build_mask(con, min_months=0)


def test_report_dict_has_parameters_old_rule(con):
    result = mask.build_mask(con, grid_deg=0.01, rule=OLD)
    rep = result.to_report()
    assert rep["parameters"] == {
        "rule": "seasonal-offseason",
        "grid_deg": 0.01,
        "min_years": 3,
        "months": [1, 2, 3, 7, 8, 9],
        "time_basis": "local_solar_datetime",
        "source_view": "hotspots_filtered",
    }
    assert rep["n_masked_cells"] == 1
    assert set(rep["share_removed_by_platform"]) == {"Aqua", "SNPP"}


# --------------------------------------------------------------------------------------------
# D-024 year-round rule (default).
# --------------------------------------------------------------------------------------------


def _month_rows(cell, platform, year_months):
    """One detection on the 10th of each (year, month) pair."""
    return [
        {"platform": platform, "lat": cell[0], "lon": cell[1], "local": f"{y}-{m:02d}-10 13:00"}
        for y, m in year_months
    ]


FOREST = (29.0012, 79.0012)  # Feb-Apr every year, 2013-2018
PADDY = (30.7012, 75.7012)  # Sep-Nov every year, 2013-2018
DOUBLE_CROP = (31.2012, 74.2012)  # Apr-May + Oct-Nov every year (rice-wheat field)
KILN = (31.6012, 74.3012)  # 8 months a year, 2014-2017
THREE_YEARS = (32.0012, 73.0012)  # year-round in exactly 3 years
TWO_YEARS = (32.1012, 73.1012)  # year-round in 2 years, seasonal in 4 more
SPARSE = (32.2012, 73.2012)  # 3 isolated months (Jan, May, Sep) in 5 years


def _year_round_rows():
    rows = []
    years = range(2013, 2019)
    rows += _month_rows(FOREST, "SNPP", [(y, m) for y in years for m in (2, 3, 4)])
    rows += _month_rows(PADDY, "Aqua", [(y, m) for y in years for m in (9, 10, 11)])
    rows += _month_rows(DOUBLE_CROP, "SNPP", [(y, m) for y in years for m in (4, 5, 10, 11)])
    kiln_months = (1, 2, 3, 4, 5, 6, 11, 12)
    rows += _month_rows(KILN, "SNPP", [(y, m) for y in range(2014, 2018) for m in kiln_months])
    rows += _month_rows(KILN, "Aqua", [(2015, 1), (2015, 3)])
    spread = (1, 4, 7, 10)  # four seasons: no two 3-month windows cover it
    rows += _month_rows(THREE_YEARS, "Terra", [(y, m) for y in (2013, 2016, 2020) for m in spread])
    rows += _month_rows(THREE_YEARS, "Terra", [(2014, 10), (2014, 11)])
    rows += _month_rows(TWO_YEARS, "SNPP", [(y, m) for y in (2013, 2014) for m in spread])
    rows += _month_rows(TWO_YEARS, "SNPP", [(y, m) for y in range(2015, 2019) for m in (10, 11)])
    rows += _month_rows(SPARSE, "SNPP", [(y, m) for y in years for m in (1, 5, 9)])
    return rows


@pytest.fixture
def con_yr():
    c = duckdb.connect()
    c.register("hotspots_filtered", make_detections(_year_round_rows()))
    return c


def _cell(coord, grid=0.01):
    return (mask.cell_index(coord[0], grid), mask.cell_index(coord[1], grid))


def _masked(result):
    return {(r.cell_lat, r.cell_lon) for r in result.cells.itertuples()}


@pytest.mark.parametrize(
    ("months", "expected"),
    [
        ((2, 3, 4), False),  # one season
        ((9, 10, 11), False),  # paddy season
        ((4, 5, 10, 11), False),  # rice-wheat: two seasons
        ((2, 3, 4, 9, 10, 11), False),  # forest season + paddy season, 6 months
        ((11, 12, 1, 2), False),  # wraps the year end: two windows (Nov-Jan, Feb-Apr)
        ((1, 5, 9), False),  # escapes two windows but only 3 months
        ((1, 4, 7, 10), True),  # four seasons
        ((1, 2, 3, 4, 5, 6, 11, 12), True),  # kiln, 8 months
        ((1, 2, 3, 5, 6, 7, 9), True),  # 7 months never fit in 6
        (tuple(range(1, 13)), True),
    ],
)
def test_is_year_round(months, expected):
    assert mask.is_year_round(months) is expected


def test_is_year_round_thresholds_configurable():
    assert mask.is_year_round((1, 5, 9), min_months=3) is True
    assert mask.is_year_round((4, 5, 10, 11), max_seasons=1) is True
    assert mask.is_year_round((1, 4, 7, 10), season_len=4) is False


def test_year_round_is_default_rule(con_yr):
    assert mask.build_mask(con_yr).rule == "year-round"


def test_seasonal_forest_cell_not_masked(con_yr):
    assert _cell(FOREST) not in _masked(mask.build_mask(con_yr))


def test_paddy_cell_not_masked(con_yr):
    assert _cell(PADDY) not in _masked(mask.build_mask(con_yr))


def test_double_crop_cell_not_masked(con_yr):
    assert _cell(DOUBLE_CROP) not in _masked(mask.build_mask(con_yr))


def test_sparse_three_month_cell_not_masked(con_yr):
    assert _cell(SPARSE) not in _masked(mask.build_mask(con_yr))


def test_kiln_cell_masked_with_years_and_months(con_yr):
    cells = mask.build_mask(con_yr).cells
    row = cells[(cells.cell_lat == _cell(KILN)[0]) & (cells.cell_lon == _cell(KILN)[1])].iloc[0]
    assert row["n_years"] == 4
    assert list(row["years"]) == [2014, 2015, 2016, 2017]
    assert row["n_detections"] == 8 * 4 + 2


def test_exactly_min_years_masked_fewer_not(con_yr):
    got = _masked(mask.build_mask(con_yr))
    assert _cell(THREE_YEARS) in got  # 3 year-round years (2013, 2016, 2020), not consecutive
    assert _cell(TWO_YEARS) not in got  # 2 year-round years; 4 seasonal years do not count
    assert got == {_cell(KILN), _cell(THREE_YEARS)}


def test_min_years_configurable_year_round(con_yr):
    assert _cell(TWO_YEARS) in _masked(mask.build_mask(con_yr, min_years=2))
    assert _cell(THREE_YEARS) not in _masked(mask.build_mask(con_yr, min_years=4))
    assert _cell(KILN) in _masked(mask.build_mask(con_yr, min_years=4))
    assert _masked(mask.build_mask(con_yr, min_years=5)) == set()


def test_months_split_across_platforms_still_count(con_yr):
    # One cell-year's months may come from different platforms (one static list, D-022).
    c = duckdb.connect()
    cell = (33.0012, 72.0012)
    rows = []
    for y in (2013, 2014, 2015):
        rows += _month_rows(cell, "Aqua", [(y, 1), (y, 4)])
        rows += _month_rows(cell, "SNPP", [(y, 7), (y, 10)])
    c.register("hotspots_filtered", make_detections(rows))
    assert _masked(mask.build_mask(c)) == {_cell(cell)}


def test_year_round_share_removed_per_platform(con_yr):
    result = mask.build_mask(con_yr)
    # Kiln: 32 SNPP + 2 Aqua. THREE_YEARS: 12 + 2 Terra.
    assert result.removed == {"Aqua": 2, "SNPP": 32, "Terra": 14}


def test_report_dict_has_parameters_year_round(con_yr):
    rep = mask.build_mask(con_yr).to_report()
    assert rep["parameters"] == {
        "rule": "year-round",
        "grid_deg": 0.01,
        "min_years": 3,
        "min_months": 4,
        "season_len": 3,
        "max_seasons": 2,
        "time_basis": "local_solar_datetime",
        "source_view": "hotspots_filtered",
    }
    assert rep["n_masked_cells"] == 2


def test_write_and_load_roundtrip_keeps_rule(con_yr, tmp_path):
    result = mask.build_mask(con_yr)
    cells_path, report_path = mask.write_outputs(result, tmp_path)
    loaded = mask.load_mask(cells_path, report_path)
    assert loaded.rule == "year-round"
    assert (loaded.min_months, loaded.season_len, loaded.max_seasons) == (4, 3, 2)
    mask.apply_mask(con_yr, loaded)
    n = con_yr.execute("SELECT count(*) FROM hotspots_masked_flags WHERE in_persistent_mask")
    assert n.fetchone()[0] == 48


def test_cli_rule_flag(tmp_path, monkeypatch, con_yr):
    from blindspot import ingest

    monkeypatch.setattr(ingest, "connect", lambda _path: con_yr)
    assert mask.main(["--out", str(tmp_path), "--rule", OLD]) == 0
    assert json.loads((tmp_path / mask.MASK_REPORT_FILE).read_text())["parameters"]["rule"] == OLD
    assert mask.main(["--out", str(tmp_path)]) == 0
    rep = json.loads((tmp_path / mask.MASK_REPORT_FILE).read_text())
    assert rep["parameters"]["rule"] == "year-round"
