"""Cross-check the browser's custom-AOI harmonized series against an independent Python
computation (D-036): same tiles, factors from calibration_factors.parquet, ORIGINAL (unsimplified)
Punjab polygons via shapely. Run after e2e/run.mjs:
    .venv/bin/python web/e2e/check_custom_aoi.py
"""

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pipeline"))
from blindspot.boundaries import find_shape, load_shapes  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ART = Path(__file__).parent / "artifacts"


def browser_csv(name: str) -> pd.Series:
    df = pd.read_csv(ART / name, comment="#")
    return df.set_index("month")["value"]


def main() -> int:
    w, s, e, n = json.loads((ART / "box.json").read_text())["bbox"]
    tiles = str(REPO / "web/public/data/tiles/year=*/*.parquet")
    pts = duckdb.execute(
        "SELECT lat, lon, strftime(acq_date, '%Y-%m') ym "
        "FROM read_parquet(?, hive_partitioning=false) "
        "WHERE platform='Aqua' AND lon BETWEEN ? AND ? AND lat BETWEEN ? AND ? "
        "AND acq_date < DATE '2012-01-01'",
        [tiles, w, e, s, n],
    ).df()
    shapes = load_shapes(REPO / "data/raw/boundaries")
    pk = find_shape(shapes, "PAK", "ADM1", "Punjab").geometry
    ind = find_shape(shapes, "IND", "ADM1", "Punjab").geometry
    p = shapely.points(pts.lon, pts.lat)
    pts["region"] = "rest_of_box"
    pts.loc[shapely.intersects(ind, p), "region"] = "IN_Punjab"
    pts.loc[shapely.intersects(pk, p), "region"] = "PK_Punjab"
    fac = pd.read_parquet(REPO / "data/processed/harmonized/calibration_factors.parquet")
    fac = fac[(fac.unit == "hotspots") & (fac.pair == "Aqua->SNPP")][["region", "month", "factor"]]
    pts["month"] = pts.ym.str[5:].astype(int)
    pts = pts.merge(fac, on=["region", "month"], how="left")
    py = pts.groupby("ym")["factor"].sum().round(1)
    br = browser_csv("box-calendar-harmonized.csv")
    br_aqua = browser_csv("box-calendar-aqua.csv")
    common = [m for m in py.index if m in br.index]
    diff = (br.loc[common].astype(float) - py.loc[common]).abs()
    rel = diff / py.loc[common].clip(lower=1)
    cnt = pts.groupby("ym").size()
    aqua_ok = all(int(br_aqua.loc[m]) == int(cnt.loc[m]) for m in cnt.index if m in br_aqua.index)
    out = {
        "months_compared": len(common),
        "max_abs_diff": float(diff.max()),
        "max_rel_diff": float(rel.max()),
        "months_differing_gt_0_1": int((diff > 0.11).sum()),
        "aqua_counts_match": aqua_ok,
        "detections_region_mismatch_note": (
            "browser uses simplified Punjab polygons (calibration.json "
            "polygon_simplify_tolerance_deg); border points may get the other factor"
        ),
    }
    print(json.dumps(out, indent=1))
    (ART / "custom_aoi_check.json").write_text(json.dumps(out, indent=1))
    # Acceptance (D-036): Aqua counts identical; at most 2 of the months differ, by < 5%.
    return (
        0 if aqua_ok and out["months_differing_gt_0_1"] <= 2 and out["max_rel_diff"] < 0.05 else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
