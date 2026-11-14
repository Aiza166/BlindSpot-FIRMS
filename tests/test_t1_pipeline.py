"""End-to-end smoke test: mask -> regions -> calibrate -> t1 -> report on synthetic data.

TEST FIXTURES ONLY. Detections are drawn from a seeded RNG inside hand-drawn squares that
stand in for provinces; nothing here is FIRMS or geoBoundaries data.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from blindspot import calibrate, mask, regions, report_t1, t1
from blindspot.boundaries import geojson_name
from conftest import make_detections

PK = (70.0, 30.0, 72.0, 31.0)  # lon0, lat0, lon1, lat1
IN = (74.0, 30.0, 76.0, 31.0)
SD = (65.0, 25.0, 66.0, 26.0)


def _sq(b):
    x0, y0, x1, y1 = b
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def _write_boundaries(d):
    d.mkdir(parents=True)
    sets = {
        ("PAK", "ADM1"): [("Punjab", "PK1", PK), ("Sindh", "PK2", SD)],
        ("IND", "ADM1"): [("Punjab", "IN1", IN)],
        ("PAK", "ADM2"): [("Lahore-ish", "PKD1", PK)],
        ("IND", "ADM2"): [("Amritsar-ish", "IND1", IN)],
    }
    for (iso, adm), feats in sets.items():
        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"shapeName": n, "shapeID": i},
                    "geometry": _sq(b),
                }
                for n, i, b in feats
            ],
        }
        (d / geojson_name(iso, adm)).write_text(json.dumps(fc))
    (d / "manifest.json").write_text("{}")


def _detections():
    rng = np.random.default_rng(42)
    rows = []

    def add(platform, box, day, n, hour):
        for _ in range(n):
            rows.append(
                {
                    "platform": platform,
                    "lat": round(rng.uniform(box[1] + 0.01, box[3] - 0.01), 4),
                    "lon": round(rng.uniform(box[0] + 0.01, box[2] - 0.01), 4),
                    "local": f"{day} {hour}",
                }
            )

    for year in range(2003, 2026):
        for day in pd.date_range(f"{year}-10-01", f"{year}-11-30").strftime("%Y-%m-%d"):
            add("Aqua", PK, day, int(rng.poisson(6)), "13:30")
            add("Aqua", IN, day, int(rng.poisson(6)), "13:30")
            add("Aqua", SD, day, 1, "13:30")
            if year >= 2012:
                add("SNPP", PK, day, int(rng.poisson(18)), "13:20")
                add("SNPP", IN, day, int(rng.poisson(18)), "13:20")
                add("SNPP", SD, day, 1, "13:20")
            if year >= 2019:
                add("NOAA20", PK, day, int(rng.poisson(12)), "12:40")
                add("NOAA20", SD, day, 1, "12:40")
    return make_detections(rows)


def _write_hotspots(df, root):
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_to_dataset(table, root, partition_cols=["year", "platform"])


def test_end_to_end(tmp_path):
    hot = tmp_path / "processed" / "hotspots"
    proc = tmp_path / "processed"
    bdir = tmp_path / "raw" / "boundaries"
    rdir = proc / "regions"
    hdir = proc / "harmonized"
    _write_hotspots(_detections(), hot)
    _write_boundaries(bdir)
    assert mask.main(["--hotspots", str(hot), "--out", str(proc)]) == 0
    assert (
        regions.main(["--hotspots", str(hot), "--boundaries", str(bdir), "--out", str(rdir)]) == 0
    )
    meta = json.loads((rdir / "regions.json").read_text())
    assert meta["pk_punjab_shape_id"] == "PK1" and meta["in_punjab_shape_id"] == "IN1"
    args = ["--hotspots", str(hot), "--mask-dir", str(proc), "--regions", str(rdir)]
    assert calibrate.main([*args, "--out", str(hdir)]) == 0
    out_json = proc / "results" / "t1.json"
    assert (
        t1.main(
            [*args, "--harmonized", str(hdir), "--boundaries", str(bdir), "--out", str(out_json)]
        )
        == 0
    )
    res = json.loads(out_json.read_text())

    fac = {
        (f["region"], f["month"]): f
        for f in res["calibration_factors"]
        if f["pair"] == "Aqua->SNPP" and f["unit"] == "hotspots"
    }
    assert 2.6 < fac[("PK_Punjab", 11)]["factor"] < 3.4  # synthetic truth: 18 / 6 = 3
    assert (
        fac[("PK_Punjab", 11)]["lo"]
        < fac[("PK_Punjab", 11)]["factor"]
        < fac[("PK_Punjab", 11)]["hi"]
    )
    for r in ("PK_Punjab", "IN_Punjab"):
        v = res["verdict_primary"][r]
        assert v["status"] == "provisional pending T2"
        assert set(res["results"]) == {"hotspots", "celldays_0.05", "celldays_0.1", "celldays_0.25"}
        assert res["results"]["hotspots"][r]["heldout"]["n"] == 4
    assert res["provenance"]["inputs"]["hotspots"]["sha256"]

    harm = pd.read_parquet(hdir / calibrate.HARMONIZED_FILE)
    pk = harm[(harm.level == "CALIB") & (harm.shape_id == "PK_Punjab")].set_index(["year", "month"])
    assert pk.loc[(2005, 11), "source_platform"] == "Aqua"
    assert pk.loc[(2013, 11), "source_platform"] == "SNPP"
    assert "NOAA20" not in set(pk.source_platform)  # files end before the S-NPP cut-over
    raw = pd.read_parquet(hdir / calibrate.MONTHLY_RAW_FILE)
    a05 = raw[(raw.shape_id == "PK_Punjab") & (raw.platform == "Aqua") & (raw.year == 2005)]
    f11 = fac[("PK_Punjab", 11)]["factor"]
    assert pk.loc[(2005, 11), "value"] == a05[a05.month == 11].n.iloc[0] * f11
    dist = harm[(harm.level == "ADM2") & (harm.shape_id == "PKD1")].set_index(["year", "month"])
    assert dist.loc[(2005, 11), "value"] == pk.loc[(2005, 11), "value"]

    md = report_t1.render(res)
    step = res["results"]["hotspots"]["PK_Punjab"]["step_2012"]
    assert f"{step['ratio']:.3f}" in md
    assert "provisional pending T2" in md
