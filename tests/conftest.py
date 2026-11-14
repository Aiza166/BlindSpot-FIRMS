"""Shared pytest fixtures.

TEST FIXTURES ONLY. Every CSV in tests/fixtures/ (files named fixture_*.csv) and every
DataFrame built here is hand-written to exercise code paths. Their columns follow the FIRMS
schemas in docs/DATA_SCHEMA.md, but the rows are invented: they are not FIRMS data and must
never be used as, or quoted as, results.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


def make_detections(rows: list[dict]) -> pd.DataFrame:
    """Build a normalised-looking hotspot table from a few hand-written rows.

    Each row needs platform, lat, lon and local (local solar time, ISO string); the rest is
    filled with values that pass every filter, unless the row overrides them.
    """
    out = []
    for i, r in enumerate(rows):
        local = pd.Timestamp(r["local"])
        utc = (local - pd.to_timedelta(r["lon"] * 240, unit="s")).tz_localize("UTC")
        base = {
            "platform": r["platform"],
            "instrument": "MODIS" if r["platform"] in ("Terra", "Aqua") else "VIIRS",
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "acq_datetime_utc": utc,
            "local_solar_datetime": local,
            "acq_date": utc.date(),
            "daynight": "D",
            "confidence_raw": "90",
            "confidence_class": "high",
            "frp": 10.0,
            "scan": 1.0,
            "track": 1.0,
            "type": 0,
            "version": "6.1",
            "processing": "standard",
            "source_file": r.get("source_file", "fixture_synthetic.csv"),
            "source_row": i + 1,
            "passes_standard": True,
            "passes_type": True,
            "passes_conf": True,
            "passes_conf_robust": True,
            "in_box": True,
            "year": utc.year,
        }
        base.update({k: v for k, v in r.items() if k not in ("local",)})
        out.append(base)
    df = pd.DataFrame(out)
    df["type"] = df["type"].astype("Int8")
    return df
