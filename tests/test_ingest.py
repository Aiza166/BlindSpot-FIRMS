"""Tests for blindspot.ingest. All inputs are hand-written fixtures (see conftest.py)."""

from __future__ import annotations

import json
import shutil

import pandas as pd
import pytest

from blindspot import ingest
from blindspot.ingest import Box, SchemaError


@pytest.fixture
def modis(fixtures_dir):
    return ingest.normalize_file(fixtures_dir / "fixture_modis_country.csv")


@pytest.fixture
def viirs(fixtures_dir):
    return ingest.normalize_file(fixtures_dir / "fixture_viirs_snpp_country.csv")


# ---------- schema normalisation ----------


def test_output_columns_are_the_normalised_schema(modis, viirs):
    for df in (modis, viirs):
        assert list(df.columns) == list(ingest.NORMALIZED_COLUMNS)


def test_modis_platforms_and_instrument(modis):
    assert modis["platform"].tolist() == ["Aqua", "Terra", "Terra", "Aqua", "Aqua"]
    assert set(modis["instrument"]) == {"MODIS"}


def test_viirs_platform_and_instrument(viirs):
    assert set(viirs["platform"]) == {"SNPP"}
    assert set(viirs["instrument"]) == {"VIIRS"}


def test_noaa20_code_maps_to_platform(fixtures_dir):
    df = ingest.normalize_file(fixtures_dir / "fixture_viirs_noaa20_nrt.csv")
    assert set(df["platform"]) == {"NOAA20"}


def test_detect_instrument_without_instrument_column():
    cols = ["latitude", "longitude", "bright_ti4", "bright_ti5"]
    assert ingest.detect_instrument(cols, None, "x.csv") == "VIIRS"
    cols = ["latitude", "longitude", "brightness", "bright_t31"]
    assert ingest.detect_instrument(cols, None, "x.csv") == "MODIS"
    assert ingest.detect_instrument(["latitude"], None, "modis_2010_Pakistan.csv") == "MODIS"
    with pytest.raises(SchemaError):
        ingest.detect_instrument(["latitude"], None, "unknown.csv")


def test_missing_required_column_raises_clear_error(fixtures_dir):
    with pytest.raises(SchemaError, match="frp"):
        ingest.normalize_file(fixtures_dir / "fixture_modis_missing_frp.csv")


def test_unknown_satellite_code_raises():
    raw = _raw_modis_frame(satellite="X")
    with pytest.raises(SchemaError, match="satellite"):
        ingest.normalize(raw, "fixture_inline.csv")


def test_instrument_mismatch_raises():
    raw = _raw_modis_frame(satellite="N")  # VIIRS code in a MODIS file
    with pytest.raises(SchemaError, match="instrument"):
        ingest.normalize(raw, "fixture_inline.csv")


def test_header_is_case_insensitive(tmp_path, fixtures_dir):
    text = (fixtures_dir / "fixture_modis_country.csv").read_text()
    header, rest = text.split("\n", 1)
    p = tmp_path / "fixture_upper.csv"
    p.write_text(header.upper() + "\n" + rest)
    df = ingest.normalize_file(p)
    assert len(df) == 5


def test_header_only_file_gives_empty_table(tmp_path, fixtures_dir):
    header = (fixtures_dir / "fixture_viirs_snpp_country.csv").read_text().split("\n")[0]
    p = tmp_path / "viirs-snpp_2012_Pakistan.csv"
    p.write_text(header + "\n")
    df = ingest.normalize_file(p)
    assert len(df) == 0
    assert list(df.columns) == list(ingest.NORMALIZED_COLUMNS)


def test_source_file_and_row_recorded(modis):
    assert set(modis["source_file"]) == {"fixture_modis_country.csv"}
    assert modis["source_row"].tolist() == [1, 2, 3, 4, 5]


# ---------- time ----------


def test_acq_time_without_leading_zeros(modis):
    # acq_time "45" means 00:45 UTC.
    row = modis.iloc[4]
    assert row["acq_datetime_utc"] == pd.Timestamp("2015-11-03 00:45", tz="UTC")


def test_local_solar_time_is_utc_plus_lon_over_15(modis):
    row = modis.iloc[0]  # 08:30 UTC at 74.3 E -> +4.9533 h
    expected = pd.Timestamp("2015-11-01 08:30") + pd.to_timedelta(74.3 / 15, unit="h")
    assert abs(row["local_solar_datetime"] - expected) < pd.Timedelta("1ms")
    assert row["local_solar_datetime"].tzinfo is None


def test_local_solar_time_whole_hours():
    utc = pd.Series(pd.to_datetime(["2020-01-01 22:00", "2020-01-01 00:00"]).tz_localize("UTC"))
    lon = pd.Series([75.0, -30.0])
    out = ingest.local_solar_datetime(utc, lon)
    assert out.tolist() == [pd.Timestamp("2020-01-02 03:00"), pd.Timestamp("2019-12-31 22:00")]


def test_year_is_utc_year(modis):
    assert set(modis["year"]) == {2015}


# ---------- confidence ----------


@pytest.mark.parametrize(
    ("value", "cls", "passes"),
    [
        ("0", "low", False),
        ("29", "low", False),
        ("30", "nominal", True),
        ("79", "nominal", True),
        ("80", "high", True),
        ("100", "high", True),
        ("abc", None, False),
    ],
)
def test_modis_confidence(value, cls, passes):
    c, p, _ = ingest.modis_confidence(pd.Series([value]))
    assert (c.iloc[0] if pd.notna(c.iloc[0]) else None) == cls
    assert bool(p.iloc[0]) is passes


@pytest.mark.parametrize(
    ("value", "cls", "passes", "robust"),
    [
        ("l", "low", False, True),
        ("n", "nominal", True, True),
        ("h", "high", True, True),
        ("low", "low", False, True),
        ("nominal", "nominal", True, True),
        ("HIGH", "high", True, True),
        ("x", None, False, False),
    ],
)
def test_viirs_confidence(value, cls, passes, robust):
    c, p, r = ingest.viirs_confidence(pd.Series([value]))
    assert (c.iloc[0] if pd.notna(c.iloc[0]) else None) == cls
    assert bool(p.iloc[0]) is passes
    assert bool(r.iloc[0]) is robust


def test_confidence_flags_on_files(modis, viirs):
    assert modis["passes_conf"].tolist() == [True, False, True, True, True]
    assert viirs["confidence_class"].tolist() == ["nominal", "low", "high", "nominal"]
    assert viirs["passes_conf"].tolist() == [True, False, True, True]
    assert viirs["passes_conf_robust"].tolist() == [True, True, True, True]
    assert modis["confidence_raw"].iloc[0] == "85"


# ---------- type / standard / box ----------


def test_type_filter(modis, viirs):
    assert modis["passes_type"].tolist() == [True, True, False, True, True]
    assert viirs["passes_type"].tolist() == [True, True, True, False]


def test_missing_type_column_fails_type_flag(fixtures_dir):
    df = ingest.normalize_file(fixtures_dir / "fixture_viirs_noaa20_nrt.csv")
    assert df["type"].isna().all()
    assert not df["passes_type"].any()


def test_processing_level_from_version(fixtures_dir, modis):
    nrt = ingest.normalize_file(fixtures_dir / "fixture_viirs_noaa20_nrt.csv")
    assert set(nrt["processing"]) == {"NRT"}
    assert not nrt["passes_standard"].any()
    assert set(modis["processing"]) == {"standard"}
    assert modis["passes_standard"].all()


@pytest.mark.parametrize(
    ("version", "level"),
    [
        ("6.1", "standard"),
        ("2", "standard"),
        ("2.0NRT", "NRT"),
        ("6.1RT", "RT"),
        ("6.1URT", "URT"),
        ("garbage", None),
    ],
)
def test_processing_level(version, level):
    out = ingest.processing_level(pd.Series([version])).iloc[0]
    assert (out if pd.notna(out) else None) == level


def test_box_filter(modis):
    # row 4 is at 85E/25N (outside); row 5 sits exactly on the 60E/23N corner (inside).
    assert modis["in_box"].tolist() == [True, True, True, False, True]


def test_box_is_configurable(fixtures_dir):
    df = ingest.normalize_file(
        fixtures_dir / "fixture_modis_country.csv", box=Box(74.35, 80, 23, 37)
    )
    assert df["in_box"].tolist() == [False, True, True, False, False]


def test_filters_never_drop_rows(modis):
    assert len(modis) == 5


def test_filtered_view_combines_flags(modis):
    out = ingest.filtered_view(modis)
    # passes all: row1 (Aqua high), row5 (corner). Row2 conf, row3 type, row4 box fail.
    assert out["source_row"].tolist() == [1, 5]


def test_filtered_view_can_allow_nrt(fixtures_dir):
    nrt = ingest.normalize_file(fixtures_dir / "fixture_viirs_noaa20_nrt.csv")
    assert len(ingest.filtered_view(nrt)) == 0
    assert len(ingest.filtered_view(nrt, require_standard=False, require_type=False)) == 2


# ---------- writing Parquet + DuckDB views ----------


def test_ingest_dir_writes_partitioned_parquet(tmp_path, fixtures_dir):
    raw = tmp_path / "raw"
    (raw / "modis" / "2015").mkdir(parents=True)
    (raw / "viirs-snpp" / "2016").mkdir(parents=True)
    shutil.copy(fixtures_dir / "fixture_modis_country.csv", raw / "modis" / "2015")
    shutil.copy(fixtures_dir / "fixture_viirs_snpp_country.csv", raw / "viirs-snpp" / "2016")
    out = tmp_path / "hotspots"
    summary = ingest.ingest_dir(raw, out)
    assert summary["n_files"] == 2
    assert summary["n_rows"] == 9
    parts = sorted(p.relative_to(out).parent.as_posix() for p in out.rglob("*.parquet"))
    assert parts == [
        "year=2015/platform=Aqua",
        "year=2015/platform=Terra",
        "year=2016/platform=SNPP",
    ]
    log = json.loads((out / ingest.INGEST_LOG).read_text())
    assert {f["source_file"] for f in log["files"]} == {
        "fixture_modis_country.csv",
        "fixture_viirs_snpp_country.csv",
    }

    con = ingest.connect(out)
    assert con.execute("SELECT count(*) FROM hotspots").fetchone()[0] == 9
    # MODIS rows 1 and 5 + VIIRS rows 1 and 3 pass every filter.
    assert con.execute("SELECT count(*) FROM hotspots_filtered").fetchone()[0] == 4


def test_ingest_dir_rerun_does_not_duplicate(tmp_path, fixtures_dir):
    raw = tmp_path / "raw"
    raw.mkdir()
    shutil.copy(fixtures_dir / "fixture_modis_country.csv", raw)
    out = tmp_path / "hotspots"
    ingest.ingest_dir(raw, out)
    ingest.ingest_dir(raw, out)
    con = ingest.connect(out)
    assert con.execute("SELECT count(*) FROM hotspots").fetchone()[0] == 5


def test_ingest_dir_refuses_to_clear_foreign_directory(tmp_path, fixtures_dir):
    raw = tmp_path / "raw"
    raw.mkdir()
    shutil.copy(fixtures_dir / "fixture_modis_country.csv", raw)
    out = tmp_path / "not_ours"
    out.mkdir()
    (out / "keep.txt").write_text("x")
    with pytest.raises(FileExistsError):
        ingest.ingest_dir(raw, out)


def test_duplicates_flagged_not_dropped(tmp_path, fixtures_dir):
    raw = tmp_path / "raw"
    raw.mkdir()
    shutil.copy(fixtures_dir / "fixture_modis_country.csv", raw / "a.csv")
    shutil.copy(fixtures_dir / "fixture_modis_country.csv", raw / "b.csv")
    out = tmp_path / "hotspots"
    ingest.ingest_dir(raw, out)
    con = ingest.connect(out)
    assert con.execute("SELECT count(*) FROM hotspots").fetchone()[0] == 10
    assert con.execute("SELECT count(*) FROM hotspots WHERE is_duplicate").fetchone()[0] == 5
    assert con.execute("SELECT count(*) FROM hotspots_filtered").fetchone()[0] == 2


def test_ingest_dir_with_no_csv_raises(tmp_path):
    (tmp_path / "raw").mkdir()
    with pytest.raises(FileNotFoundError):
        ingest.ingest_dir(tmp_path / "raw", tmp_path / "out")


# ---------- helpers ----------


def _raw_modis_frame(satellite: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "latitude": ["31.5"],
            "longitude": ["74.3"],
            "brightness": ["330"],
            "scan": ["1"],
            "track": ["1"],
            "acq_date": ["2015-11-01"],
            "acq_time": ["0830"],
            "satellite": [satellite],
            "instrument": ["MODIS"],
            "confidence": ["85"],
            "version": ["6.1"],
            "bright_t31": ["300"],
            "frp": ["25"],
            "daynight": ["D"],
            "type": ["0"],
        }
    )
