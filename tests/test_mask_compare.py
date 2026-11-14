"""Smoke test of blindspot.mask_compare on hand-written detections (see conftest.py)."""

from __future__ import annotations

import duckdb

from blindspot import mask_compare
from conftest import make_detections


def _rows():
    rows = []
    # Static-looking cell inside the Punjab core: Jan, Apr, Jul, Oct in 2013-2015.
    for y in (2013, 2014, 2015):
        for m in (1, 4, 7, 10):
            rows.append(
                {
                    "platform": "SNPP",
                    "lat": 31.0012,
                    "lon": 74.0012,
                    "local": f"{y}-{m:02d}-10 13:00",
                }
            )
    # Seasonal cell: Feb only, 2013-2015 -> masked by the old rule, kept by the new one.
    for y in (2013, 2014, 2015):
        rows.append(
            {"platform": "Aqua", "lat": 30.0012, "lon": 73.0012, "local": f"{y}-02-10 13:30"}
        )
        rows.append(
            {"platform": "Aqua", "lat": 30.0012, "lon": 73.0012, "local": f"{y}-11-10 13:30"}
        )
    return rows


def test_compare_old_vs_new():
    con = duckdb.connect()
    con.register("hotspots_filtered", make_detections(_rows()))
    rep = mask_compare.compare(con)
    old, new = rep["rules"]["old"], rep["rules"]["new"]
    assert old["n_masked_cells"] == 2
    assert new["n_masked_cells"] == 1
    assert new["overall"]["Aqua"]["removed"] == 0
    assert new["overall"]["SNPP"]["share"] == 1.0
    assert old["punjab_core_oct_nov"]["Aqua"] == {"total": 3, "removed": 3, "share": 1.0}
    assert new["punjab_core_oct_nov"]["SNPP"] == {"total": 3, "removed": 3, "share": 1.0}
    assert new["snpp_by_month"][10] == {"total": 3, "removed": 3, "share": 1.0}
    top = new["top_cells"][0]
    assert (top["centre_lat"], top["centre_lon"]) == (31.005, 74.005)
    assert top["months_all_years"] == [1, 4, 7, 10]
    assert top["qualifying_years"] == [2013, 2014, 2015]
    md = mask_compare.render_markdown(rep)
    assert "| Old | 2 |" in md and "| New | 1 |" in md
